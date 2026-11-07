# Heap-overflow detection vs. redzone size\n
Write at a fixed offset past a 16-byte allocation, under the same
`ASAN_OPTIONS` as the cost measurement, with ASLR disabled.\n
| max_redzone | offset +40 | offset +100 | offset +200 |
|---|---|---|---|
| 32  | **detected** | **detected** | **detected** |
| 64  | **detected** | **detected** | **detected** |
| 128  | **detected** | **detected** | **detected** |
| 256  | **detected** | **detected** | **detected** |

A short redzone finds fewer of these writes: the overflow has to land
inside the poisoned region to be caught (paper Sec. 3.5).
