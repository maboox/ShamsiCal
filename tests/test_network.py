import json
import socket

import pytest

from shamsical import network as net


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "javascript:alert(1)",
        "http://example.com/feed",
        "https://127.0.0.1/a",
        "https://169.254.169.254/latest",
        "https://10.0.0.1/",
        "https://localhost/",
        "https://example.local/",
        "https://user:password@example.org/feed",
        "https://example.org:8443/feed",
        "https://example.org/\nheader",
    ],
)
def test_untrusted_urls_rejected(url):
    with pytest.raises(net.NetworkError):
        net.safe_url(url)


def test_relative_fragment_normalization():
    assert net.safe_url("https://example.org/feed#section") == "https://example.org/feed"


def test_dns_private_mixed_answers_blocked(monkeypatch):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *a, **k: [(2, 1, 6, "", ("8.8.8.8", 443)), (2, 1, 6, "", ("127.0.0.1", 443))],
    )
    with pytest.raises(net.NetworkError):
        net.public_addresses("example.org")


class Response:
    def __init__(self, status=200, headers=None, chunks=None):
        self.status = status
        self.headers = headers or {}
        self.chunks = iter(chunks or [b"ok", b""])
        self.closed = False

    def read(self, *_args, **_kwargs):
        return next(self.chunks, b"")

    def close(self):
        self.closed = True


def fake_pool(monkeypatch, responses):
    calls = []
    monkeypatch.setattr(net, "public_addresses", lambda _: ["8.8.8.8"])

    class Pool:
        def __init__(self, host, **kwargs):
            calls.append((host, kwargs))

        def urlopen(self, method, path, **kwargs):
            calls.append((method, path, kwargs))
            return responses.pop(0)

        def close(self):
            pass

    monkeypatch.setattr(net.urllib3, "HTTPSConnectionPool", Pool)
    return calls


def test_transport_pins_ip_and_verifies_hostname(monkeypatch):
    response = Response()
    calls = fake_pool(monkeypatch, [response])
    assert net.fetch("https://example.org/feed") == b"ok"
    assert calls[0][0] == "8.8.8.8"
    assert calls[0][1]["server_hostname"] == "example.org"
    assert calls[0][1]["assert_hostname"] == "example.org"
    assert calls[0][1]["cert_reqs"] == "CERT_REQUIRED"
    assert calls[1][2]["retries"] is False
    assert response.closed


def test_redirect_to_private_address_blocked(monkeypatch):
    response = Response(302, {"Location": "https://127.0.0.1/secret"})
    fake_pool(monkeypatch, [response])
    with pytest.raises(net.NetworkError):
        net.fetch("https://example.org/feed")
    assert response.closed


@pytest.mark.parametrize(
    "response",
    [
        Response(200, {"Content-Length": str(net.MAX_RESPONSE + 1)}),
        Response(200, {"Content-Encoding": "gzip"}),
        Response(200, chunks=[b"x" * (net.MAX_RESPONSE + 1)]),
    ],
)
def test_resource_limits(monkeypatch, response):
    fake_pool(monkeypatch, [response])
    with pytest.raises(net.NetworkError):
        net.fetch("https://example.org/feed")


def test_authenticated_redirect_never_forwards_key(monkeypatch):
    responses = [Response(302, {"Location": "https://other.org/"})]
    calls = fake_pool(monkeypatch, responses)
    with pytest.raises(net.NetworkError):
        net.fetch("https://api.together.xyz/v1/chat/completions", token="test-value", payload={})
    assert len(calls) == 2


def test_feed_html_and_unsafe_links_are_removed(monkeypatch):
    xml = b'<rss version="2.0"><channel><title>Test</title><item><title>&lt;b&gt;Hello&lt;/b&gt;</title><link>file:///private.txt</link><description>&lt;img src="file:///private"&gt;World</description></item></channel></rss>'
    monkeypatch.setattr(net, "fetch", lambda _: xml)
    assert net.read_feed("https://example.org/rss")[0] == {"title": "Hello", "summary": "World", "link": ""}


def test_failed_event_schema_does_not_become_empty_success(monkeypatch):
    from shamsical.calendar import today

    monkeypatch.setattr(net, "fetch", lambda _: json.dumps({"status": False}).encode())
    with pytest.raises(net.NetworkError):
        net.read_events(today())


def test_xml_entity_feed_rejected(monkeypatch):
    monkeypatch.setattr(net, "fetch", lambda _: b'<!DOCTYPE x [<!ENTITY y SYSTEM "file:///secret">]>')
    with pytest.raises(net.NetworkError):
        net.read_feed("https://example.org/rss")


def test_feed_body_cannot_be_treated_as_local_path(monkeypatch, tmp_path):
    secret = tmp_path / "private.xml"
    secret.write_text(
        '<rss version="2.0"><channel><title>Private</title><item><title>Secret</title></item></channel></rss>'
    )
    monkeypatch.setattr(net, "fetch", lambda _: str(secret).encode())
    with pytest.raises(net.NetworkError):
        net.read_feed("https://example.org/rss")


@pytest.mark.parametrize("url", ["https://127.1/", "https://0177.0.0.1/", "https://0x7f.0.0.1/"])
def test_noncanonical_numeric_hosts_rejected(url):
    with pytest.raises(net.NetworkError):
        net.safe_url(url)


def test_utf16_doctype_blocked(monkeypatch):
    monkeypatch.setattr(net, "fetch", lambda _: '<!DOCTYPE x [<!ENTITY y "expanded">]>'.encode("utf-16"))
    with pytest.raises(net.NetworkError):
        net.read_feed("https://example.org/rss")
