**MLA 原理图解：KV缓存压缩 93%**

> 这是DeepSeek-V2论文中的MLA架构图。传统Multi-Head Attention需要为每个注意力头存储完整的Key和Value向量。MLA的核心思想：将KV投影到一个低秩潜向量(latent vector)，只缓存这个压缩后的向量。需要时再通过上投影重建完整KV。结果：KV缓存压缩约93%，推理内存需求大幅降低。

> 旁边的对比图展示了MHA→GQA→MQA→MLA的演进路径。MLA在极小缓存下保持了MHA级性能。

> 【引导看图】注意Figure 3中MLA的压缩-重建机制——这是DeepSeek效率革命的核心。