# Mixamo internal API (no public API; stable since years — verified 2026‑09‑02)
Headers: `Authorization: Bearer <access_token>` (from `localStorage.access_token` after browser login), `X-Api-Key: mixamo2`, JSON.
Base `https://www.mixamo.com/api/v1`
- Search: `GET /products?page=1&limit=96&order=&type=Character|Motion|MotionPack&query=zombie`
- Details (for gms_hash params): `GET /products/{id}?similar=0&character_id={char}`
- Export: `POST /animations/export` body `{gms_hash:[{model-id, mirror:false, trim:[0,100], overdrive:0, params:"0,0", arm-space:0, inplace:bool}], preferences:{format:"fbx7_2019", skin:"true|false", fps:"30", reducekf:"0"}, character_id, type:"Motion"|"Character", product_name}` → 202. Bare character: `gms_hash: []`, `type:"Character"`, `skin:"true"`.
- Poll: `GET /characters/{char}/monitor` → `status: completed` + `job_result` (S3 URL, 5‑min expiry). 3–10 s each, serialized per character.
- `params` = join of `details.gms_hash.params[*][1]`; `inplace:true` for Walk/Run/Strafe.
Known character IDs: Zombiegirl `2f8e576f-f69d-453e-830e-969a2f0217ea`, Copzombie `3d9daeb8-c2d5-45ce-b835-7cd403c72fc7`, Warzombie `3576fd60-beef-49ec-a3d0-f93231f4fc29`, Romero `576b18a3-2e3e-4f50-b665-cbca337e0757`, "Survivor" `52dcdacb-b43e-4efc-ab6d-9d2d6e09bc95` (**looks like a zombie — do not use as a human protagonist**).
License: free use inside games/films; no stand‑alone redistribution of the FBX.
