# Zen 2 DRAM counters, event by event (Ryzen 9 3900X, Linux 7.0, 2026-10-12)

Each calibration kernel (`build/traffic_calib`) is 1 GiB × 5 passes, pinned to CPU 1. Values are counts × 64 B /
(1 GiB × 5), i.e. bytes per pass. The `amd_df` events are counted system-wide; the `ls_*` events on CPU 1 only.

| event | r: read | n: fill, NT | w: fill, ordinary | b: copy, NT | a: copy, ordinary |
|---|---|---|---|---|---|
| expected DRAM bytes (read + write) | 1 | 1 | 2 | 2 | 3 |
| amd_df/dram_channel_data_controller_0 | 0.918 | 0.913 | 1.414 | 1.415 | 1.916 |
| amd_df/dram_channel_data_controller_1 | 0.918 | 0.914 | 1.415 | 1.416 | 1.916 |
| amd_df/dram_channel_data_controller_2 | 1.220 | 0.722 | 1.051 | 2.171 | 2.027 |
| amd_df/dram_channel_data_controller_3 | 1.221 | 0.711 | 1.050 | 2.173 | 2.027 |
| amd_df/dram_channel_data_controller_4 … 7 | 0 | 0 | 0 | 0 | 0 |
| ls_refills_from_sys.ls_mabresp_lcl_dram | 0.712 | 0.004 | 0.010 | 0.283 | 0.628 |
| ls_hw_pf_dc_fill.ls_mabresp_lcl_dram | 0.462 | 0.172 | 0.596 | 0.824 | 0.525 |
| ls_sw_pf_dc_fill.ls_mabresp_lcl_dram | 0 | 0 | 0 | 0 | 0 |

**Data-fabric events:**
- They come in identical pairs (0 = 1, 2 = 3), and events 4–7 never count on this 2-channel part. Summing
  all eight, as the suite did, double-counts.
- Neither live event is linear in bytes. The ordinary fill and the NT copy both move 2 bytes per byte, yet
  event 0 reads 1.41 for both. The ordinary copy moves 3 and reads 1.92.
- Events 0 and 2 also disagree with each other: for a read, 0.92 against 1.22.
- No weighting of the live events reproduces all five kernels. The counts track data-fabric activity, not
  DRAM bytes.

**Per-core fill events:**
- Demand plus hardware-prefetch fills from DRAM approximate reads for a plain read (1.17).
- They miss reads that do not fill L1: L2-prefetcher fills and read-for-ownership. The ordinary copy reads
  1.15 where its reads are 2.
- They see no writes.

**Conclusion:** Zen 2 offers no counter set that measures DRAM bytes. The suite's refusal to report traffic
for uncalibrated counters stands.
