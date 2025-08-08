import json
from datetime import datetime
from pathlib import Path

DEFAULT_CFG = {
    'sections': {
        'Unassigned': []
    },
    'comments': {},
    'locked': False,
    'last_opened': None,
}
CFG_VERSION = 1


def cfg_path_for(txt_path: Path) -> Path:
    return txt_path.with_suffix('.cfg')


def load_cfg(path: Path):
    if not path.exists():
        return DEFAULT_CFG | {'version': CFG_VERSION}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        cfg.setdefault('version', CFG_VERSION)
        cfg.setdefault('sections', {'Unassigned': []})
        cfg.setdefault('locked', False)
        cfg.setdefault('comments', {})
        return cfg
    except Exception:
        return DEFAULT_CFG | {'version': CFG_VERSION}


def save_cfg(path: Path, cfg: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2)


def reconcile_cfg_with_txt(cfg: dict, eq_names: set):
    # Remove names not in txt
    for sec in list(cfg['sections'].keys()):
        cfg['sections'][sec] = [n for n in cfg['sections'][sec] if n in eq_names]
        if sec != 'Unassigned' and not cfg['sections'][sec]:
            del cfg['sections'][sec]
    # Add names missing in cfg to Unassigned
    cfg_names = {n for lst in cfg['sections'].values() for n in lst}
    for n in sorted(eq_names - cfg_names):
        cfg.setdefault('sections', {}).setdefault('Unassigned', []).append(n)
    cfg['last_opened'] = datetime.now().isoformat()
    return cfg
