from wealth_exposure.allowlist import DEFAULT_ALLOWLIST
from wealth_exposure.consent import ClientRecord, ConsentScope
from wealth_exposure.exposure_register import ExposureRegister
from wealth_exposure.watchers.feeds import CounterpartyFilingWatcher, RegisterChangeWatcher
from wealth_exposure.watchers.runner import WatcherRunner


class StubFeed:
    def __init__(self, changes):
        self._changes = changes

    def poll(self):
        return self._changes


def _scope():
    s = ConsentScope()
    s.add_client(ClientRecord("client-1", verified=True))
    s.declare_entity("client-1", "ENT")
    s.declare_counterparty("client-1", "FIRM")
    return s


def test_register_watcher_flags_only_in_scope_entities():
    scope, reg = _scope(), ExposureRegister()
    feed = StubFeed([
        {"entity": "ENT", "summary": "PSC change"},
        {"entity": "OTHER", "summary": "not our entity"},  # must be ignored
    ])
    produced = WatcherRunner(
        [RegisterChangeWatcher(DEFAULT_ALLOWLIST, scope, feed)], reg).run_once()
    assert len(produced) == 1
    assert produced[0].client_id == "client-1"
    assert reg.for_client("client-1")[0].description == "PSC change"


def test_counterparty_watcher_attributes_to_owning_client():
    scope, reg = _scope(), ExposureRegister()
    feed = StubFeed([{"firm": "FIRM", "summary": "Qualified audit opinion filed"}])
    produced = WatcherRunner(
        [CounterpartyFilingWatcher(DEFAULT_ALLOWLIST, scope, feed)], reg).run_once()
    assert len(produced) == 1
    assert produced[0].client_id == "client-1"


def test_watcher_ignores_change_with_no_subject():
    scope, reg = _scope(), ExposureRegister()
    feed = StubFeed([{"summary": "change with no entity field"}])
    produced = WatcherRunner(
        [RegisterChangeWatcher(DEFAULT_ALLOWLIST, scope, feed)], reg).run_once()
    assert produced == []
