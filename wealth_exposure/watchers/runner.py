"""Runs a set of watchers and records the resulting flags in the exposure
register. Each produced item is already scoped to a consenting client by the
watcher's `to_exposure_items`.
"""
from __future__ import annotations


class WatcherRunner:
    def __init__(self, watchers, register):
        self.watchers = list(watchers)
        self.register = register

    def run_once(self) -> list:
        produced = []
        for watcher in self.watchers:
            for change in watcher.detect_changes():
                for item in watcher.to_exposure_items(change):
                    self.register.add(item)
                    produced.append(item)
        return produced
