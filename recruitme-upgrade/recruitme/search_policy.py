"""Translate the saved web profile into bounded worker configuration.

Pure function: no account changes, network calls, or ledger resets.
"""
from copy import deepcopy
from decimal import Decimal
from .budget import StopRun, money

DISCOVERY = {'exa_free', 'pdl_free', 'apollo', 'exa_keyed', 'exa_people', 'tavily', 'brave', 'serpapi'}


def apply_search_policy(config, profile):
    cfg = deepcopy(config)
    cap = money(profile.get('runCap'))
    if cap > min(money('5'), money(cfg['default_run_limit_usd'])):
        raise StopRun('Search budget exceeds worker ceiling')
    duration = profile.get('durationMinutes')
    if type(duration) is not int or not 1 <= duration <= 30:
        raise StopRun('Invalid search duration')
    selections = profile.get('searchProviders')
    if not isinstance(selections, list) or not 1 <= len(selections) <= len(DISCOVERY):
        raise StopRun('Select at least one supported source')
    chosen = set()
    free, paid = [], []
    for selection in selections:
        name = selection.get('id')
        if name not in DISCOVERY or name in chosen:
            raise StopRun('Unknown or duplicate source')
        chosen.add(name)
        allocation = money(selection.get('budget'))
        if allocation > money('5'):
            raise StopRun('Provider allocation exceeds ceiling')
        p = cfg['providers'].get(name)
        # Missing accounts stay visible as unavailable; never claim activation.
        if not p or not p.get('enabled') or not p.get('approved'):
            continue
        cost = money(p.get('operations', {}).get('search'))
        p['run_limit_usd'] = str(Decimal(min(allocation, cap, money(p['run_limit_usd']))) / 1000000)
        if cost == 0:
            free.append(name)
        elif cfg.get('paid_enabled') and cost <= min(allocation, cap, money(p['run_limit_usd'])):
            paid.append(name)
    for name, p in cfg['providers'].items():
        p['enabled'] = name in free + paid
    if not free and not paid:
        raise StopRun('No connected source fits this search budget')
    cfg['paid_enabled'] = bool(paid)
    cfg['default_run_limit_usd'] = str(Decimal(cap) / 1000000)
    cfg['max_run_seconds'] = min(duration * 60, int(cfg['max_run_seconds']))
    cfg['provider_priority'] = {
        'free_discovery': free,
        'low_cost_paid_discovery': sorted(paid, key=lambda name: money(cfg['providers'][name]['operations']['search'])),
        'targeted_content': [], 'finalist_enrichment': [],
    }
    cfg['web_search_policy'] = True
    return cfg
