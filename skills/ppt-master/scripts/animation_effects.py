"""Animation effect normalization, targets, and semantic pools.

Extracted from pptx_animations.py (system-optimization Phase 6 split).
Consumers: pptx_animations.py (timing/validation groups).
"""
from __future__ import annotations

import math
import random
import re
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from animation_constants import (
    ANIMATION_AFTER_EFFECTS,
    ANIMATION_ALIAS_OPTIONS,
    ANIMATION_ALIASES,
    ANIMATION_CATEGORIES,
    ANIMATION_EFFECT_OPTION_FIELDS,
    ANIMATION_MODES,
    ANIMATION_RESTARTS,
    ANIMATION_TIMING_OPTION_FIELDS,
    ANIMATION_TRIGGERS,
    ANIMATIONS,
    LEGACY_ANIMATION_KEYS,
    NATIVE_ANIMATIONS,
    _NON_CONCRETE_FONT_NAMES,
    _PRESET_CLASS_BY_CATEGORY,
    _NODE_TYPE_TRIGGERS,
    _TRIGGER_NODE_TYPES,
)
from pptx_transitions import (
    PML_NS,
    TRANSITION_ALIASES,
    TRANSITION_ALIAS_OPTIONS,
    MAX_OOXML_MILLISECONDS,
    MAX_OOXML_UNSIGNED_INT,
    validate_seconds,
)

@dataclass
class AnimationTarget:
    """Resolved object-animation request for one PowerPoint shape."""

    shape_id: int
    delay_ms: int
    effect: str
    duration_ms: int
    effect_options: Mapping[str, object]
    trigger: str = 'after-previous'
    trigger_shape_id: int | None = None
    repeat_count: float | None = None
    repeat_duration_ms: int | None = None
    auto_reverse: bool | None = None
    rewind: bool | None = None
    accelerate: float | None = None
    decelerate: float | None = None
    bounce_end: float | None = None
    restart: str | None = None
    after_effect: str = 'none'
    after_effect_color: str | None = None
    sound_relationship_id: str | None = None
    sound_name: str | None = None

    @property
    def playback_duration_ms(self) -> int:
        """Return the wall-clock duration used by after-previous scheduling."""
        one_play = self.duration_ms * (2 if self.auto_reverse else 1)
        if self.repeat_duration_ms is not None:
            return self.repeat_duration_ms
        if self.repeat_count is not None:
            return max(1, round(one_play * self.repeat_count))
        return one_play


@dataclass(frozen=True)
class AnimationRowSummary:
    """Read-back summary for one object-animation row in the animation pane."""

    shape_id: int
    effect: str | None
    supported_effects: tuple[str, ...]
    preset_class: str
    trigger: str
    duration_ms: int | None
    offset_ms: int
    preset_id: int
    preset_subtype: int
    filter_name: str | None
    effect_options: Mapping[str, object]
    trigger_shape_id: int | None
    repeat_count: float | None
    repeat_duration_ms: int | None
    auto_reverse: bool
    rewind: bool
    accelerate: float
    decelerate: float
    bounce_end: float
    restart: str
    after_effect: str
    after_effect_color: str | None
    sound_relationship_id: str | None
    sound_name: str | None
    playback_duration_ms: int | None


@dataclass(frozen=True)
class AnimationSequenceSummary:
    """Read-back summary for the logical object sequence on one slide."""

    timing_count: int
    trigger: str | None
    rows: tuple[AnimationRowSummary, ...]
    audio_target_ids: tuple[int, ...]


def _qn(namespace: str, tag: str) -> str:
    return f'{{{namespace}}}{tag}'


def _local_name(tag: str) -> str:
    return tag.rsplit('}', 1)[-1]


def normalize_animation_effect(
    effect: object,
    *,
    allow_none: bool = True,
    allow_modes: bool = True,
) -> str | None:
    """Return a supported effect/mode without silently substituting another."""
    if effect is None or effect == 'none':
        if allow_none:
            return None
        raise ValueError('animation effect is required')
    if not isinstance(effect, str):
        raise ValueError(f'animation effect must be a string: {effect!r}')
    if effect in ANIMATION_ALIASES:
        return ANIMATION_ALIASES[effect]
    if effect in NATIVE_ANIMATIONS:
        return effect
    if allow_modes and effect in ANIMATION_MODES:
        return effect
    valid = list(ANIMATIONS)
    if allow_modes:
        valid.extend(ANIMATION_MODES)
    if allow_none:
        valid.append('none')
    raise ValueError(
        f'unknown animation effect {effect!r}; valid effects: {", ".join(valid)}'
    )


def _finite_number(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'{field} must be a finite number: {value!r}')
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f'{field} must be a finite number: {value!r}')
    return number


def _normalize_animation_color(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(
            f'{field} must be #RRGGBB or theme:<scheme-color>: {value!r}'
        )
    if re.fullmatch(r'#[0-9A-Fa-f]{6}', value):
        return value.upper()
    if re.fullmatch(
        r'theme:(?:dk1|lt1|dk2|lt2|tx1|tx2|bg1|bg2|accent[1-6]|'
        r'hlink|folHlink)',
        value,
    ):
        return value
    raise ValueError(
        f'{field} must be #RRGGBB or theme:<scheme-color>: {value!r}'
    )


def _normalize_powerpoint_font_name(value: object, field: str) -> str:
    """Return one concrete PowerPoint font name without checking installation."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f'{field} must be one concrete PowerPoint font name: {value!r}'
        )
    normalized = value.strip()
    if len(normalized) > 255:
        raise ValueError(f'{field} exceeds 255 characters')
    if ',' in normalized:
        raise ValueError(
            f'{field} must be one concrete PowerPoint font name, '
            f'not a CSS font stack: {value!r}'
        )
    if normalized.casefold() in _NON_CONCRETE_FONT_NAMES:
        raise ValueError(
            f'{field} must be one concrete PowerPoint font name, '
            f'not a generic family or CSS-wide keyword: {value!r}'
        )
    return normalized


def normalize_animation_effect_options(
    effect: str,
    options: object = None,
) -> dict[str, object]:
    """Validate effect-specific PowerPoint EffectParameters values."""
    if effect not in NATIVE_ANIMATIONS:
        if options in (None, {}):
            return {}
        raise ValueError(
            'animation effect_options require one explicit canonical effect; '
            f'found {effect!r}'
        )
    if options is None:
        options = {}
    if not isinstance(options, Mapping):
        raise ValueError(f'animation effect_options must be an object: {options!r}')

    option_specs = NATIVE_ANIMATIONS[effect]['effectOptions']
    unknown = set(options) - set(option_specs)
    if unknown:
        unsupported = ', '.join(sorted(unknown))
        supported = ', '.join(option_specs) or '(none)'
        raise ValueError(
            f'animation effect {effect!r} does not support effect option(s): '
            f'{unsupported}; supported options: {supported}'
        )
    missing_required = sorted(
        name
        for name, spec in option_specs.items()
        if spec.get('required') and name not in options
    )
    if missing_required:
        required_fields = ', '.join(
            f'effect_options.{name}' for name in missing_required
        )
        raise ValueError(
            f'animation effect {effect!r} requires {required_fields}'
        )

    normalized: dict[str, object] = {}
    for name, value in options.items():
        spec = option_specs[name]
        option_type = spec['type']
        field = f'animation effect_options.{name}'
        if option_type == 'enum':
            key = str(value)
            if isinstance(value, bool) or key not in spec['values']:
                valid = ', '.join(spec['values'])
                raise ValueError(
                    f'{field} for {effect!r} must be one of {valid}: {value!r}'
                )
            normalized[name] = (
                int(key)
                if name == 'amount' and re.fullmatch(r'\d+', key)
                else key
            )
        elif option_type == 'number':
            number = _finite_number(value, field)
            minimum = spec.get('minimum')
            maximum = spec.get('maximum')
            if minimum is not None and number < float(minimum):
                raise ValueError(
                    f'{field} for {effect!r} must be at least {minimum}: {value!r}'
                )
            if maximum is not None and number > float(maximum):
                raise ValueError(
                    f'{field} for {effect!r} must be at most {maximum}: {value!r}'
                )
            normalized[name] = number
        elif option_type == 'string':
            if name == 'font_name':
                normalized[name] = _normalize_powerpoint_font_name(value, field)
            else:
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(
                        f'{field} must be a non-empty string: {value!r}'
                    )
                normalized_value = value.strip()
                if len(normalized_value) > 255:
                    raise ValueError(f'{field} exceeds 255 characters')
                normalized[name] = normalized_value
        elif option_type == 'boolean':
            if not isinstance(value, bool):
                raise ValueError(f'{field} must be a boolean: {value!r}')
            normalized[name] = value
        elif option_type == 'color':
            normalized[name] = _normalize_animation_color(value, field)
        else:
            raise AssertionError(f'unhandled animation effect option type: {option_type}')
    return normalized


def normalize_animation_effect_request(
    effect: object,
    options: object = None,
    *,
    allow_none: bool = True,
    allow_modes: bool = True,
) -> tuple[str | None, dict[str, object]]:
    """Normalize one effect plus options, including legacy semantic aliases."""
    raw_effect = effect
    canonical = normalize_animation_effect(
        effect,
        allow_none=allow_none,
        allow_modes=allow_modes,
    )
    alias_options = (
        ANIMATION_ALIAS_OPTIONS.get(raw_effect, {})
        if isinstance(raw_effect, str)
        else {}
    )
    explicit_options: Mapping[str, object]
    if options is None:
        explicit_options = {}
    elif isinstance(options, Mapping):
        explicit_options = options
    else:
        raise ValueError(f'animation effect_options must be an object: {options!r}')
    for name, alias_value in alias_options.items():
        if name in explicit_options and explicit_options[name] != alias_value:
            raise ValueError(
                f'legacy animation effect {raw_effect!r} implies '
                f'effect_options.{name}={alias_value!r}, which conflicts with '
                f'{explicit_options[name]!r}'
            )
    merged = {**alias_options, **explicit_options}
    if canonical is None or canonical in ANIMATION_MODES:
        if merged:
            raise ValueError(
                'animation effect_options require one explicit canonical effect; '
                f'found {canonical or "none"!r}'
            )
        return canonical, {}
    return canonical, normalize_animation_effect_options(canonical, merged)


def normalize_animation_trigger(trigger: object) -> str:
    """Return a supported PowerPoint Start mode or raise a precise error."""
    if not isinstance(trigger, str):
        raise ValueError(f'animation trigger must be a string: {trigger!r}')
    if trigger not in ANIMATION_TRIGGERS:
        raise ValueError(
            f'unknown animation trigger {trigger!r}; valid triggers: '
            f'{", ".join(ANIMATION_TRIGGERS)}'
        )
    return trigger


def _seconds_to_ms(value: object, field: str, *, allow_zero: bool) -> int:
    seconds = validate_seconds(value, field, allow_zero=allow_zero)
    raw_milliseconds = seconds * 1000
    if (
        not math.isfinite(raw_milliseconds)
        or raw_milliseconds > MAX_OOXML_MILLISECONDS
    ):
        raise ValueError(f'{field} exceeds the OOXML millisecond limit: {value!r}')
    milliseconds = int(raw_milliseconds)
    return milliseconds if allow_zero else max(1, milliseconds)


def animation_seconds_to_milliseconds(
    value: object,
    field: str,
    *,
    allow_zero: bool,
) -> int:
    """Convert validated animation seconds to the OOXML millisecond range."""
    return _seconds_to_ms(value, field, allow_zero=allow_zero)


def _positive_shape_id(value: object, field: str = 'animation shape_id') -> int:
    if isinstance(value, bool):
        raise ValueError(f'{field} must be a positive integer: {value!r}')
    if isinstance(value, int):
        shape_id = value
    elif isinstance(value, str) and re.fullmatch(r'[1-9]\d*', value):
        shape_id = int(value)
    else:
        raise ValueError(f'{field} must be a positive integer: {value!r}')
    if shape_id <= 0 or shape_id > MAX_OOXML_UNSIGNED_INT:
        raise ValueError(f'{field} must be a positive integer: {value!r}')
    return shape_id


def _non_negative_milliseconds(value: object, field: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f'{field} must be a non-negative integer: {value!r}')
    if isinstance(value, int):
        milliseconds = value
    elif isinstance(value, str) and re.fullmatch(r'\d+', value):
        milliseconds = int(value)
    else:
        raise ValueError(f'{field} must be a non-negative integer: {value!r}')
    if milliseconds < 0 or milliseconds > MAX_OOXML_MILLISECONDS:
        raise ValueError(
            f'{field} must be between 0 and {MAX_OOXML_MILLISECONDS}: {value!r}'
        )
    return milliseconds


def _optional_bool(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f'{field} must be a boolean: {value!r}')
    return value


def _optional_ratio(value: object, field: str) -> float:
    ratio = _finite_number(value, field)
    if ratio < 0 or ratio > 1:
        raise ValueError(f'{field} must be between 0 and 1: {value!r}')
    return ratio


def _normalize_repeat_count(value: object) -> float:
    count = _finite_number(value, 'animation repeat_count')
    if count <= 0 or count * 1000 > MAX_OOXML_UNSIGNED_INT:
        raise ValueError(
            'animation repeat_count must be positive and fit the OOXML range: '
            f'{value!r}'
        )
    return count


def _normalize_after_effect(value: object) -> tuple[str, str | None]:
    if value is None:
        return 'none', None
    if isinstance(value, str):
        effect_type = value
        color = None
    elif isinstance(value, Mapping):
        unknown = set(value) - {'type', 'color'}
        if unknown:
            raise ValueError(
                'animation after_effect has unknown field(s): '
                + ', '.join(sorted(unknown))
            )
        effect_type = value.get('type', 'none')
        color = value.get('color')
    else:
        raise ValueError(
            f'animation after_effect must be a string or object: {value!r}'
        )
    if effect_type not in ANIMATION_AFTER_EFFECTS:
        raise ValueError(
            f'animation after_effect.type must be one of '
            f'{", ".join(ANIMATION_AFTER_EFFECTS)}: {effect_type!r}'
        )
    if effect_type == 'dim':
        if color is None:
            raise ValueError('animation dim after_effect requires color')
        return effect_type, _normalize_animation_color(
            color,
            'animation after_effect.color',
        )
    if color is not None:
        raise ValueError(
            f'animation after_effect.color is valid only with type "dim": {color!r}'
        )
    return effect_type, None


def _normalize_sound(value: object) -> tuple[str | None, str | None]:
    if value is None:
        return None, None
    if not isinstance(value, Mapping):
        raise ValueError(
            'low-level animation sound must be an object with '
            'relationship_id and name'
        )
    unknown = set(value) - {'relationship_id', 'name'}
    if unknown:
        raise ValueError(
            'low-level animation sound has unknown field(s): '
            + ', '.join(sorted(unknown))
        )
    relationship_id = value.get('relationship_id')
    name = value.get('name')
    if not isinstance(relationship_id, str) or not re.fullmatch(
        r'rId[1-9]\d*',
        relationship_id,
    ):
        raise ValueError(
            'low-level animation sound relationship_id must match rIdN: '
            f'{relationship_id!r}'
        )
    if not isinstance(name, str) or not name.strip():
        raise ValueError(
            f'low-level animation sound name must be non-empty: {name!r}'
        )
    return relationship_id, name


def _normalize_target_mapping(
    target: Mapping[str, object],
    default_duration_ms: int,
    default_trigger: str,
) -> AnimationTarget:
    allowed = {
        'shape_id',
        'delay_ms',
        'effect',
        'duration',
        'effect_options',
        'trigger',
        'trigger_shape_id',
        *ANIMATION_TIMING_OPTION_FIELDS,
        'after_effect',
        'sound',
    }
    unknown = set(target) - allowed
    if unknown:
        raise ValueError(
            'animation target has unknown field(s): ' + ', '.join(sorted(unknown))
        )
    shape_id = _positive_shape_id(target.get('shape_id'))
    delay_ms = _non_negative_milliseconds(
        target.get('delay_ms', 0),
        'animation target delay_ms',
    )
    effect, effect_options = normalize_animation_effect_request(
        target.get('effect'),
        target.get('effect_options'),
        allow_none=False,
        allow_modes=False,
    )
    duration_ms = default_duration_ms
    if target.get('duration') is not None:
        duration_ms = _seconds_to_ms(
            target.get('duration'),
            'animation target duration',
            allow_zero=False,
        )
    trigger_shape_id = (
        _positive_shape_id(
            target['trigger_shape_id'],
            'animation target trigger_shape_id',
        )
        if 'trigger_shape_id' in target
        else None
    )
    if trigger_shape_id == shape_id:
        raise ValueError(
            'animation trigger_shape_id must target a different shape'
        )
    target_trigger = (
        normalize_animation_trigger(target['trigger'])
        if 'trigger' in target
        else default_trigger
    )
    if trigger_shape_id is not None:
        if 'trigger' in target and target_trigger != 'on-click':
            raise ValueError(
                'animation target with trigger_shape_id must use '
                'trigger "on-click"'
            )
        target_trigger = 'on-click'
    repeat_count = (
        _normalize_repeat_count(target['repeat_count'])
        if 'repeat_count' in target
        else None
    )
    repeat_duration_ms = (
        _seconds_to_ms(
            target['repeat_duration'],
            'animation repeat_duration',
            allow_zero=False,
        )
        if 'repeat_duration' in target
        else None
    )
    if repeat_count is not None and repeat_duration_ms is not None:
        raise ValueError(
            'animation repeat_count and repeat_duration are mutually exclusive'
        )
    auto_reverse = (
        _optional_bool(target['auto_reverse'], 'animation auto_reverse')
        if 'auto_reverse' in target
        else None
    )
    rewind = (
        _optional_bool(target['rewind'], 'animation rewind')
        if 'rewind' in target
        else None
    )
    accelerate = (
        _optional_ratio(target['accelerate'], 'animation accelerate')
        if 'accelerate' in target
        else None
    )
    decelerate = (
        _optional_ratio(target['decelerate'], 'animation decelerate')
        if 'decelerate' in target
        else None
    )
    if (
        accelerate is not None
        and decelerate is not None
        and accelerate + decelerate > 1
    ):
        raise ValueError(
            'animation accelerate + decelerate must not exceed 1'
        )
    bounce_end = (
        _optional_ratio(target['bounce_end'], 'animation bounce_end')
        if 'bounce_end' in target
        else None
    )
    if bounce_end and decelerate:
        raise ValueError(
            'animation bounce_end and decelerate are mutually exclusive '
            'in PowerPoint'
        )
    restart = target.get('restart')
    if restart is not None and restart not in ANIMATION_RESTARTS:
        raise ValueError(
            f'animation restart must be one of '
            f'{", ".join(ANIMATION_RESTARTS)}: {restart!r}'
        )
    after_effect, after_effect_color = _normalize_after_effect(
        target.get('after_effect')
    )
    sound_relationship_id, sound_name = _normalize_sound(target.get('sound'))
    return AnimationTarget(
        shape_id=shape_id,
        delay_ms=delay_ms,
        effect=effect,
        duration_ms=duration_ms,
        effect_options=effect_options,
        trigger=target_trigger,
        trigger_shape_id=trigger_shape_id,
        repeat_count=repeat_count,
        repeat_duration_ms=repeat_duration_ms,
        auto_reverse=auto_reverse,
        rewind=rewind,
        accelerate=accelerate,
        decelerate=decelerate,
        bounce_end=bounce_end,
        restart=restart,
        after_effect=after_effect,
        after_effect_color=after_effect_color,
        sound_relationship_id=sound_relationship_id,
        sound_name=sound_name,
    )


def _normalize_target(
    target: Sequence[object] | Mapping[str, object],
    default_duration_ms: int,
    default_trigger: str = 'after-previous',
) -> AnimationTarget:
    if isinstance(target, Mapping):
        return _normalize_target_mapping(
            target,
            default_duration_ms,
            default_trigger,
        )
    if isinstance(target, (str, bytes)) or not isinstance(target, Sequence):
        raise ValueError(f'animation target must be a 3- or 4-item sequence: {target!r}')
    if len(target) not in (3, 4):
        raise ValueError(f'animation target must contain 3 or 4 items: {target!r}')
    shape_id = _positive_shape_id(target[0])
    delay_ms = _non_negative_milliseconds(target[1], 'animation target delay_ms')
    effect, effect_options = normalize_animation_effect_request(
        target[2],
        allow_none=False,
        allow_modes=False,
    )
    duration_ms = default_duration_ms
    if len(target) == 4 and target[3] is not None:
        duration_ms = _seconds_to_ms(
            target[3],
            'animation target duration',
            allow_zero=False,
        )
    return AnimationTarget(
        shape_id=shape_id,
        delay_ms=delay_ms,
        effect=effect,
        duration_ms=duration_ms,
        effect_options=effect_options,
        trigger=default_trigger,
    )

# Pool used by 'mixed' / 'random' modes. Every entry is a canonical
# PowerPoint-authored preset; compatibility aliases never enter selection.
_MIXED_POOL = [
    'entrance_blinds', 'entrance_checkerboard', 'entrance_dissolve',
    'entrance_fly', 'entrance_ascend', 'entrance_random_bars',
    'entrance_box', 'entrance_split', 'entrance_strips', 'entrance_wedge',
    'entrance_wheel', 'entrance_wipe', 'entrance_expand', 'entrance_fade',
    'entrance_swivel', 'entrance_zoom',
]

# Small modern pool used by 'auto' mode when the group id matches no semantic
# pattern. Restricted to four widely supported, restrained effects so the
# fallback cycle never produces PowerPoint-era visuals.
_AUTO_POOL = [
    'entrance_fade',
    'entrance_wipe',
    'entrance_fly',
    'entrance_zoom',
]

# Image-only diversity pool. Image-like groups (`hero`, `figure-`, `image`,
# `img-`, `kpi`) deliberately cycle through a richer set of visual effects
# rather than mapping to a single effect: images are visual focal points, so
# variation is desirable on them even when surrounding information-dense
# elements (titles, charts, lists) stay reserved. Pool members are chosen for
# image-friendly motion — no PowerPoint-era patterns (``entrance_blinds`` /
# ``entrance_checkerboard`` / ``entrance_random_bars`` / ``entrance_wedge``)
# that would dominate raster content.
_IMAGE_POOL = [
    'entrance_zoom',
    'entrance_dissolve',
    'entrance_circle',
    'entrance_box',
    'entrance_diamond',
    'entrance_wheel',
]
_IMAGE_KEYWORDS: tuple[str, ...] = ('hero', 'figure-', 'image', 'img-', 'kpi')

# Ordered (substring, effect) patterns consumed by 'auto' mode for non-image
# groups. The first matching substring in the lowercased group id wins;
# ordering matters where substrings could overlap (e.g. 'title' before 'item'
# prevents 'item-title' from being misread as a list item). All substrings are
# lowercase. Image-like ids are handled separately via ``_IMAGE_POOL`` because
# they cycle rather than map to a single effect.
_SEMANTIC_PATTERNS: list[tuple[tuple[str, ...], str]] = [
    (
        ('title', 'chapter-', 'section-', 'cover-', 'tagline', 'subtitle'),
        'entrance_fade',
    ),
    (
        ('chart', 'table', 'legend', 'timeline', 'track'),
        'entrance_wipe',
    ),
    (('card-', 'pillar-', 'item-', 'step-', 'stage-', 'tier-',
      'principle-', 'q-', 'schema-'),                           'entrance_fly'),
    (('takeaway', 'callout', 'quote', 'source', 'conclusion', 'note',
      'try-at-home'),                                           'entrance_fade'),
]


