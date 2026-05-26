---
title: "Congestion Control Breakdown in AI Training Networks"
date: 2026-05-26
draft: false
author: "Michael Olagbemiro"
tags: ["networking", "RoCE", "ECN", "PFC", "BGP", "AI infrastructure"]
description: "ECN incast collapse at 4:1 sender ratio — reproducing the instability Meta observed abandoning DCQCN at 400G scale."
showToc: true
TocOpen: false
cover:
    image: /images/fig1-incast-sweep.png
    alt: "ECN incast collapse at 4 senders"
    caption: "Throughput collapses 23% at N=4 senders — feedback loop over-reaction"
---

📄 **[Download full paper (PDF)](/papers/congestion-control-breakdown.pdf)** | 💻 **[Code and data on GitHub](https://github.com/michael-olagbemiro/roce-lab)**

---

## What this is about

When thousands of GPUs synchronize gradient updates during AI training, every node sends simultaneously. That synchronized burst — incast — is the defining traffic pattern of distributed training, and it is exactly what standard congestion control was not designed for.

This post documents what happens when you try to demonstrate PFC and ECN congestion control on virtual switching platforms, hit two platform walls, and extract something more useful than the original experiment would have produced: a precise characterisation of ECN's incast breakdown threshold and its architectural dependency on sustained queue pressure.

---

## Three findings

**1. ECN incast collapse at 4:1 fan-in**

Running 1 to 4 simultaneous senders toward a single receiver, with HTB+RED+ECN on each sender:

| Senders | Throughput (Mbits/s) | Retransmits | CE marks |
|---------|---------------------|-------------|----------|
| 1 | 48.0 ± 0.03 | 0 | 839 ± 14 |
| 2 | 96.2 ± 0.05 | 0 | 1,763 ± 16 |
| 3 | 97.9 ± 0.99 | 2,198 ± 54 | 1,812 ± 55 |
| 4 | 75.2 ± 2.44 | 2,220 ± 98 | 1,547 ± 105 |

At N=4, throughput collapsed 23% (t(4)=14.9, p<0.001). The most telling observation: CE marks *decreased* at N=4 despite more congestion — the signature of feedback loop over-reaction. This is qualitatively the same instability Meta observed with DCQCN at 400G scale (SIGCOMM 2024).

![Incast sweep](/images/fig1-incast-sweep.png)

**2. ECN's architectural dependency on queue pressure**

Without an HTB rate limiter, ECN produced zero CE marks — even with 4 simultaneous senders at full rate. Not fewer marks. Zero.

ECN requires three conditions simultaneously: a queue management mechanism, watching a real buffer, under sustained pressure. Remove any one and ECN is completely blind regardless of traffic intensity. This explains why virtual switching platforms cannot demonstrate native ECN marking — no ASIC buffer model means no queue for RED to watch.

**3. The silent RED misconfiguration**

RED initialised silently as a no-op when the burst parameter was too small: zero marks, full throughput, no error. Indistinguishable from correct operation without checking CE counters explicitly.

Fix: `burst ≥ ⌈min_th / avpkt⌉ × 2` — not documented in the tc-red man page.

---

## Threshold sensitivity

| Min threshold | CE marks | Throughput |
|--------------|----------|------------|
| 10 KB | 3,893 ± 63 | 95.9 Mbps |
| 30 KB | 1,646 ± 47 | 96.2 Mbps |
| 50 KB | 1,140 ± 23 | 96.9 Mbps |
| 100 KB | 0 | 97.0 Mbps |

71% fewer marks from 10KB to 50KB threshold, less than 1% throughput difference. Above ~100KB: ECN blind zone — zero marks, looks identical to correct operation.

![Threshold sensitivity](/images/fig2-threshold-sweep.png)

---

## PFC: structure and effect

SR Linux virtual does not generate PFC pause frames autonomously. Demonstrated two ways:

**Frame structure:** Scapy-generated 802.3x frames. Opcode 0x0101, priority enable 0x0008 (priority 3 = RoCE lossless queue), quanta 0xFFFF (~33ms at 10Gbps). SR Linux correctly terminated at ingress — link-local by IEEE 802.3x, identical to physical switch behaviour.

**Behavioral effect:** 500ms hard pause applied mid-flow. Throughput dropped to exactly 0.0 Mbps for five consecutive 100ms intervals across all 3 trials. Full recovery within 700ms.

![PFC behavioral effect](/images/fig6-pfc-behavioral.png)

---

## What virtual platforms can and can't tell you

| Capability | Virtual | Real ASIC |
|------------|---------|-----------|
| BGP / routing validation | ✅ | ✅ |
| ECN mechanism (with Linux tc) | ✅ | ✅ |
| ECN incast breakdown threshold | ✅ | ✅ |
| PFC frame structure | ✅ | ✅ |
| Autonomous PFC generation | ❌ | ✅ |
| Native ECN at switch egress | ❌ | ✅ |
| Microburst timing accuracy | ❌ | ✅ |

---

## Lab

- 2 spine + 2 leaf (Nokia SR Linux, containerlab 0.75.0)
- 5 hosts (network-multitool)
- eBGP: AS 65001/65002 leaves, AS 65000 spines
- GCP c3-standard-22 (Intel — AMD N2D silently breaks nested virtualisation)
- One `containerlab deploy` → fully configured fabric

**[Full paper (PDF)](/papers/congestion-control-breakdown.pdf)** | **[GitHub](https://github.com/michael-olagbemiro/roce-lab)**