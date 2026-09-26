"""Prepare only the newly verified time precision for three existing records."""
from delivery_exame_cotec_prepare import main

TARGETS = {
    'objetiva_open': ('tp-tcj-63d6b0d7101d5715b855b7a178fecada-1', '2026-05-12T13:00:00-03:00', '2026-06-10T13:00:00-03:00', '2026-07-05'),
    'institutomais_open': ('tp-tcj-582b5040ab985e598614a89b1605b4cd-1', '2026-01-12T10:00:00-03:00', '2026-02-12T17:00:00-03:00', '2026-03-22'),
    'ibam_open': ('tp-tcj-828fe3e4f0f45800a4e0b50dbdb4c0c3-1', '2026-08-10T00:00:00-03:00', '2026-10-08T23:59:00-03:00', '2026-11-29'),
}

if __name__ == '__main__':
    main(TARGETS, 'delivery-three-precise-proposed-20260909-v2.json')
