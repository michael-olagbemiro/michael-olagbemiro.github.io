---
title: "NCCL Collective Communication Performance on 8x A100 SXM4 NVSwitch"
draft: false
author: "Michael Olagbemiro"
tags: ["GPU", "NCCL", "distributed training", "AI infrastructure", "benchmarking"]
description: "Empirical benchmarking of NCCL algorithm and protocol selection on 8x A100 SXM4 NVSwitch — Ring-Tree crossover at 4-8KB, LL protocol 61% bandwidth penalty, and two undocumented performance anomalies."
showToc: true
TocOpen: false
cover:
    image: /images/plotA_ring_tree_auto_8x.png
    alt: "Ring vs Tree vs Auto on 8x A100 NVSwitch"
    caption: "Tree outperforms Ring between 4KB and 8KB. Ring dominates everywhere else."
---

**[Download full paper (PDF)](/papers/nccl-benchmarks.pdf)** | **[Code and data on GitHub](https://github.com/michael-olagbemiro/nccl-benchmarks)**

---

## What this is about

Every distributed training job is secretly a communication problem. When 8 GPUs synchronise gradients after each training step, NCCL makes two decisions that most engineers never examine: which algorithm to use (Ring or Tree) and which protocol to use (LL, LL128, or Simple). Those decisions determine whether you saturate your NVSwitch fabric or leave most of it idle.

This post presents empirical measurements of those decisions on 8x NVIDIA A100 SXM4 80GB GPUs connected via NVSwitch, sweeping message sizes from 8 bytes to 8GB. The findings include two previously undocumented performance anomalies and a precise decision table for practitioners.

---

## Hardware topology

![Hardware topology](/images/topology_diagram.png)

All experiments ran on a single server with 8x A100 SXM4 80GB GPUs connected via NVSwitch fabric, providing approximately 600 GB/s aggregate bidirectional bandwidth. Every GPU has a direct full-bandwidth path to every other GPU simultaneously.

---

## Finding 1 — Ring vs Tree crossover at 4-8 KB

![Ring vs Tree vs Auto](/images/plotA_ring_tree_auto_8x.png)

The NCCL documentation says Tree is better for small messages and Ring for large — but it does not say where the crossover is on 8x A100 NVSwitch. The answer is between 4KB and 8KB.

Below 4KB all three algorithms are latency-dominated. The minimum observed latency is approximately 48-50 us regardless of message size, reflecting the fixed overhead of coordinating 8 GPUs. In this regime algorithm choice has no measurable effect.

Tree outperforms Ring at 4KB and 8KB. The advantage comes from Tree's lower hop count: 6 steps for 8 GPUs versus Ring's 14, reducing coordination latency at the point where transfer time is beginning to emerge from the latency floor.

Above 16KB Ring decisively outperforms Tree. Ring peaks at 232.0 GB/s while Tree peaks at 183.9 GB/s — a 20.7% gap driven by Ring's full bandwidth utilisation versus Tree's root bottleneck.

**The Tree collapse at 64MB** is a previously undocumented anomaly. Tree drops 26.7% at 64MB before recovering — consistent with a chunk size boundary in NCCL's Tree implementation. Auto correctly avoids Tree at this size.

---

## Finding 2 — LL protocol imposes a 61% bandwidth penalty

![Protocol comparison](/images/plotB_protocols_8x.png)

![Protocol peaks](/images/plotD2_protocol_peaks_8x.png)

Below 16KB all three protocols are comparable. Above 16KB the difference becomes severe.

LL hits an asymptotic ceiling of 90.4 GB/s regardless of message size. The theoretical flag overhead of LL is 33% but the observed penalty is 61.2% relative to Auto's peak of 232.8 GB/s, indicating secondary effects beyond raw flag bandwidth.

LL128 reaches 172.0 GB/s — a 26.1% penalty despite only 6.25% theoretical flag overhead.

Crossover thresholds: LL128 beats LL at 16KB; Auto beats LL128 at 32KB.

---

## Finding 3 — Auto selection is consistently optimal

Auto matched or exceeded every manually forced configuration at every message size. At peak, Auto achieves 232.8 GB/s — 0.8 GB/s above forced Ring. This marginal advantage reflects internal optimisations — channel count tuning, chunk size adjustment — that are not accessible through the NCCL_ALGO environment variable.

Do not override NCCL_ALGO or NCCL_PROTO in production.

---

## Finding 4 — AllGather anomaly at 32MB

![Collective comparison](/images/plotC_collectives_8x.png)

AllReduce peaks at 232.8 GB/s, ReduceScatter at 229.2 GB/s, AllGather at 222.9 GB/s.

AllGather drops from 88.8 GB/s at 16MB to 67.9 GB/s at 32MB before recovering strongly. This is directly relevant to FSDP users — transformer attention projection matrices for models with hidden dimension ~4096 frequently fall near 32MB.

---

## Practical decision table

| Message size | Optimal algorithm | Optimal protocol |
|-------------|-------------------|-----------------|
| < 4KB | Ring | LL |
| 4KB - 8KB | Tree | LL128 |
| 8KB - 32KB | Ring | LL128 |
| > 32KB | Ring | Auto |

In practice: use Auto for both and these choices are made correctly without manual configuration.

---

## Results summary

| Configuration | Peak bus bandwidth |
|--------------|-------------------|
| Ring | 232.0 GB/s |
| Tree | 183.9 GB/s |
| Auto | 232.8 GB/s |
| LL | 90.4 GB/s |
| LL128 | 172.0 GB/s |
| AllGather | 222.9 GB/s |
| ReduceScatter | 229.2 GB/s |

---

## Reproducing these results

All benchmark data, plotting scripts, and reproduction instructions are in the GitHub repository.

**[Full paper (PDF)](/papers/nccl-benchmarks.pdf)** | **[GitHub](https://github.com/michael-olagbemiro/nccl-benchmarks)**