---
description: >
  Implementation spec for adding img2img (image-to-image / reference image) support
  to image_gen.py. Covers CLI, manifest, backend, and test plan. Based on Yunwu API
  docs (https://yunwu.apifox.cn/doc-5459032).
---

# img2img Support Implementation

> Adds reference-image input to the image generation pipeline. Currently all backends
> are text-to-image only. This spec targets the `openai` backend (Yunwu proxy) first,
> with a generic interface other backends can implement later.

## Background

The Yunwu API (base `https://yunwu.ai`) exposes two img2img mechanisms on its
OpenAI-compatible endpoints:

| Mechanism | Endpoint | Content-Type | Use case |
|---|---|---|---|
| **Edits (file upload)** | `POST /v1/images/edits` | `multipart/form-data` | Local file → edit. Primary img2img path. |
| **Edits (URL → temp)** | `POST /v1/images/edits` | `multipart/form-data` | Remote URL → download → upload. Used for all URL references. |

Supported models for img2img: `flux-kontext-pro`, `flux-kontext-max`,
`gpt-image-1`, `grok-imagine-image-pro`. The edits endpoint also accepts an
optional `mask` file (PNG, alpha=0 = editable region).

No explicit strength/weight parameter exists — the prompt text controls the
degree of transformation.

---

## Step 1: Extend the `generate()` interface

**File**: `skills/ppt-master/scripts/image_gen.py` and all backends under
`skills/ppt-master/scripts/image_backends/`.

Add an optional `reference_image: str | None = None` parameter to every
`generate()` function signature:

```python
def generate(prompt: str,
             aspect_ratio: str = "1:1", image_size: str = "1K",
             output_dir: str = None, filename: str = None,
             model: str = None, max_retries: int = MAX_RETRIES,
             reference_image: str | None = None) -> str:
```

**Convention**: `reference_image` accepts either:
- A local file path (`/path/to/image.png`) — resolved relative to CWD
- An HTTP(S) URL (`https://example.com/ref.jpg`) — passed directly

The dispatcher in `image_gen.py` forwards the parameter through to the backend.
Backends that do not yet support img2img raise `ValueError("Backend 'X' does not
support reference_image")` when `reference_image is not None`.

---

## Step 2: Implement img2img in `backend_openai.py`

**File**: `skills/ppt-master/scripts/image_backends/backend_openai.py`

### 2.1 New helper: `_image_edits_url()`

```python
def _image_edits_url(base_url: str | None) -> str:
    """Resolve the /v1/images/edits endpoint."""
    base = (base_url or DEFAULT_BASE_URL).rstrip("/")
    if base.endswith("/images/edits"):
        return base
    return f"{base}/images/edits"
```

### 2.2 New function: `_post_image_edits()`

Handles multipart/form-data upload to `/v1/images/edits`:

```python
def _post_image_edits(api_key: str, base_url: str | None,
                      image_path_or_url: str, prompt: str,
                      model: str, aspect_ratio: str,
                      mask_path: str | None = None) -> dict:
    """POST to /v1/images/edits with multipart form data."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }
    form_data = {
        "prompt": prompt,
        "model": model,
        "n": "1",
        "aspect_ratio": aspect_ratio,
    }

    files = {}
    if _is_url(image_path_or_url):
        # Some models accept image as URL string in form field
        form_data["image"] = image_path_or_url
    else:
        # Upload local file
        files["image"] = (
            os.path.basename(image_path_or_url),
            open(image_path_or_url, "rb"),
            "application/octet-stream",
        )

    if mask_path and not _is_url(mask_path):
        files["mask"] = (
            os.path.basename(mask_path),
            open(mask_path, "rb"),
            "application/octet-stream",
        )

    response = requests.post(
        _image_edits_url(base_url),
        headers=headers,
        data=form_data if files else None,
        files=files if files else None,
        timeout=300,
    )
    # Close file handles
    for f in files.values():
        f[1].close()

    if not response.ok:
        raise http_error(response, "OpenAI image edits")
    return response.json()
```

### 2.3 New function: `_post_image_generations_with_ref()`

Handles JSON body with `image` URL field to `/v1/images/generations`:

```python
def _post_image_generations_with_ref(api_key: str, base_url: str | None,
                                      image_url: str, prompt: str,
                                      model: str, size: str) -> dict:
    """POST to /v1/images/generations with an image URL for img2img."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    request = {
        "image": image_url,
        "prompt": prompt,
        "model": model,
        "size": size,
        "n": 1,
    }
    response = requests.post(
        _image_generations_url(base_url),
        headers=headers,
        json=request,
        timeout=300,
    )
    if not response.ok:
        raise http_error(response, "OpenAI image generation (img2img)")
    return response.json()
```

### 2.4 Modify `_generate_image()` to branch on `reference_image`

Add `reference_image: str | None = None` to the signature. When non-None:

```
if reference_image is not None:
    # img2img mode
    if is_local_file(reference_image) or not is_url(reference_image):
        # Use /v1/images/edits (multipart upload)
        resp = _post_image_edits(api_key, base_url, reference_image,
                                  prompt, model, aspect_ratio)
    else:
        # Use /v1/images/generations with image URL
        resp = _post_image_generations_with_ref(api_key, base_url,
                                                  reference_image, prompt,
                                                  model, size)
    # ... resolve response (same b64_json / url handling as text2img)
```

### 2.5 Modify public `generate()` to forward `reference_image`

```python
def generate(prompt: str,
             aspect_ratio: str = "1:1", image_size: str = "1K",
             output_dir: str = None, filename: str = None,
             model: str = None, max_retries: int = MAX_RETRIES,
             reference_image: str | None = None) -> str:
    # ... existing validation ...
    # Forward to _generate_image:
    return _generate_image(api_key, prompt, aspect_ratio, image_size,
                           output_dir, filename, model, base_url,
                           reference_image=reference_image)
```

---

## Step 3: CLI support in `image_gen.py`

**File**: `skills/ppt-master/scripts/image_gen.py`

### 3.1 Add `--reference-image` argument

```python
parser.add_argument(
    "--reference-image", "-ri", default=None, metavar="PATH_OR_URL",
    help=(
        "Reference image for img2img mode. Accepts a local file path or "
        "an HTTP(S) URL. When provided, the backend uses its img2img endpoint."
    ),
)
```

### 3.2 Single-image mode: pass through

```python
backend.generate(
    prompt=args.prompt,
    aspect_ratio=args.aspect_ratio,
    image_size=args.image_size,
    output_dir=args.output,
    filename=args.filename,
    model=args.model,
    reference_image=args.reference_image,   # <-- new
)
```

### 3.3 Manifest mode: per-item `reference_image`

The `_run_manifest()` function already passes individual item fields to
`backend.generate()`. Add the manifest field to the forwarded call:

```python
saved_path = backend_module.generate(
    prompt=item["prompt"],
    aspect_ratio=item["aspect_ratio"],
    image_size=item.get("image_size", image_size),
    output_dir=output_dir,
    filename=Path(item["filename"]).stem,
    model=item.get("model", model),
    reference_image=item.get("reference_image"),   # <-- new, optional
)
```

No change to `load_manifest()` validation — `reference_image` is optional and
not in `REQUIRED_ITEM_FIELDS`.

---

## Step 4: Manifest schema update

**File**: `skills/ppt-master/references/image-generator.md` (docs update)

The `image_prompts.json` schema gains an optional field per item:

```json
{
  "items": [
    {
      "filename": "cover.png",
      "prompt": "a futuristic cityscape",
      "aspect_ratio": "16:9",
      "status": "Pending",
      "reference_image": "sources/reference_sketch.png"
    }
  ]
}
```

`reference_image` is:
- **Omitted or null**: text-to-image (default, current behavior)
- **Local path**: resolved relative to the manifest's parent directory
- **HTTP(S) URL**: passed directly to the backend

---

## Step 5: Update other backends (stub rejection)

For every backend that does NOT yet support img2img, add at the top of
`generate()`:

```python
if reference_image is not None:
    raise ValueError(
        f"Backend '{BACKEND_NAME}' does not support img2img "
        "(reference_image). Use IMAGE_BACKEND=openai with a Yunwu-compatible "
        "proxy, or remove --reference-image."
    )
```

Files to update:
- `backend_gemini.py`
- `backend_minimax.py`
- `backend_qwen.py`
- `backend_zhipu.py`
- `backend_volcengine.py`
- `backend_modelscope.py`
- `backend_stability.py`
- `backend_bfl.py`
- `backend_ideogram.py`
- `backend_siliconflow.py`
- `backend_fal.py`
- `backend_replicate.py`
- `backend_openrouter.py`

---

## Step 6: Testing

### 6.1 Manual CLI test (text2img baseline)

```bash
python3 skills/ppt-master/scripts/image_gen.py \
  "a red sports car on a mountain road" \
  --aspect_ratio 16:9 --image_size 1K \
  -o /tmp/img_test
```

Expected: image file generated, no errors.

### 6.2 Manual CLI test (img2img with local file)

```bash
python3 skills/ppt-master/scripts/image_gen.py \
  "change the car color to blue" \
  --reference-image /tmp/img_test/generated_image.png \
  --aspect_ratio 16:9 --image_size 1K \
  -o /tmp/img_test
```

Expected: new image generated based on the reference, car is now blue.

### 6.3 Manual CLI test (img2img with URL)

```bash
python3 skills/ppt-master/scripts/image_gen.py \
  "add snow to the mountain peaks" \
  --reference-image "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Camponotus_flavomarginatus_ant.jpg/330px-Camponotus_flavomarginatus_ant.jpg" \
  --aspect_ratio 1:1 --image_size 1K \
  -o /tmp/img_test
```

Expected: image edited with snow effect.

### 6.4 Manifest batch test

Create a test manifest `test_img2img_manifest.json`:

```json
{
  "items": [
    {
      "filename": "car_blue.png",
      "prompt": "change the car color to blue",
      "aspect_ratio": "16:9",
      "status": "Pending",
      "reference_image": "/tmp/img_test/generated_image.png"
    },
    {
      "filename": "new_scene.png",
      "prompt": "a beautiful landscape",
      "aspect_ratio": "16:9",
      "status": "Pending"
    }
  ]
}
```

```bash
python3 skills/ppt-master/scripts/image_gen.py \
  --manifest test_img2img_manifest.json \
  -o /tmp/img_test
```

Expected: first item uses img2img, second uses text2img. Both succeed.

---

## File change summary

| File | Change type | Description |
|---|---|---|
| `scripts/image_gen.py` | Modify | Add `--reference-image` CLI arg, forward to backend, pass through in manifest mode |
| `scripts/image_backends/backend_openai.py` | Modify | Add `_image_edits_url()`, `_post_image_edits()`, `_post_image_generations_with_ref()`; branch `_generate_image()` on `reference_image`; update `generate()` signature |
| `scripts/image_backends/backend_*.py` (13 files) | Modify | Add stub rejection for `reference_image` param |
| `references/image-generator.md` | Modify | Document `reference_image` manifest field and `--reference-image` CLI flag |

---

## Implementation order

1. `backend_openai.py` — core img2img logic (Steps 2.1–2.5)
2. `image_gen.py` — CLI + manifest forwarding (Steps 3 + 4)
3. All other backends — stub rejection (Step 5)
4. Manual testing (Step 6)
5. Documentation update
