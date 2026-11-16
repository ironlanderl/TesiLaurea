> [!warning] Time zones
> Times here are in GMT+1, times in pcaps (or at least the data from caronte) are GMT+0

# Info

| Service       | Port |
|---------------|------|
| CCForms-1     | 3001 |
| CCForms-2     | 3001 |
| CCalendar-1   | 8443 |
| CCalendar-2   | 8443 |
| Exccel-1      | 8000 |
| Exccel-2      | 8000 |
| Cooking Nonna | 2222 |

> [!NOTE] Exccel-1 Flag Format
>```
>      >>> "0P0A04P4GCS3VP1ZAYLGMIR2R9L94UC=".encode().hex()
>      '3050304130345034474353335650315a41594c474d49523252394c393455433d'
>```
> `\x22[A-Fa-f0-9]{62}3d\x22` ?

> [!NOTE] CCalendar-1 & CCalendar-2
> Caronte gives error analyzing pcaps

> [!NOTE] CCForms
> Easier to treat as the same flag storage

## 2025-06-20

| Service       | Blood | IN_MIN | IN_MAX   | OUT_MIN | OUT_MAX  |
|---------------|-------|--------|----------|---------|----------|
| CCForms-1     | 11:08 | 1.443s | 108.042s |         |          |
| CCForms-2     | 11:16 | 1.443s | 108.042s |         |          |
| CCalendar-1   | 11:18 |        |          |         |          |
| CCalendar-2   | 12:02 |        |          |         |          |
| Exccel-1      | 15:30 | 3.43s  | 83.021s  | 1.286s  | 95.677s  |
| Exccel-2      | 11:46 | 1.019s | 82.943s  |         |          |
| Cooking Nonna | 15:04 | 2.106s | 103.262s | 1.518s  | 103.314s |

## 2025-06-21

| Service       | Blood | IN_MIN | IN_MAX   | OUT_MIN | OUT_MAX  |
|---------------|-------|--------|----------|---------|----------|
| CCForms-1     | 11:04 | 1.256s | 107.871s |         |          |
| CCForms-2     | 11:04 | 1.256s | 107.871s |         |          |
| CCalendar-1   | 11:04 |        |          |         |          |
| CCalendar-2   | 11:04 |        |          |         |          |
| Exccel-1      | 11:06 | 1.748s | 83.077s  |         |          |
| Exccel-2      | 11:04 | 2.335s | 83.013s  |         |          |
| Cooking Nonna | XXXXX | 1.98s  | 103.017s | 1.447s  | 103.243s |



## 2026-06-19

| Service       | Blood | IN_MIN | IN_MAX   | OUT_MIN | OUT_MAX  |
|---------------|-------|--------|----------|---------|----------|
| CCForms-1      | 13:04 | 1.741s | 107.666s |
| CCForms-2      | 11:28 | 1.741s | 107.666s |
| CCalendar-1    | 11:22 |
| CCalendar-2    | 11:52 |
| Exccel-1       | 14:10 | 1.594s | 82.823s | 1.366s | 85.741s |
| Exccel-2       | 11:14 | 1.425s | 82.97s |
| CookingNonna-1 | 14:04 | 1.775s | 72.696s | 1.31s | 87.973s |

## 2026-06-20

| Service       | Blood | IN_MIN | IN_MAX   | OUT_MIN | OUT_MAX  |
|---------------|-------|--------|----------|---------|----------|
| CCForms-1      | 11:04 |
| CCForms-2      | 11:04 |
| CCalendar-1    | 11:04 |
| CCalendar-2    | 11:04 |
| Exccel-1       | 11:16 |
| Exccel-2       | 11:14 |
| CookingNonna-1 | 14:46 |
