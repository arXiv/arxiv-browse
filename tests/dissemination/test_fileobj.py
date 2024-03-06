from hypothesis import given
from hypothesis.strategies import text, binary

from browse.services.object_store.fileobj import MockStringFileObj, FileTransform


@given(text())
def test_filetransform(data: str) -> None:
    orig_file = MockStringFileObj("no_name.data", data=data)

    def transform(xx: bytes) -> bytes:
        return xx.decode('utf-8').lower().encode("utf-8")

    expected = transform(data.encode("utf-8"))
    new_file = FileTransform(orig_file, transform)
    transformed_data = new_file.open('rb').read()
    assert transformed_data == expected



@given(text())
def test_filetransform_fakeurls(data: str) -> None:
    orig_file = MockStringFileObj("no_name.data", data=data)

    def letters_to_fake_urls(xx: bytes) -> bytes:
        out = b""
        for byte in xx:
            if byte > 0x40 and byte < 0x5b:
                out += f'<a href="https://arxiv.org/abs/{byte}">{byte}</a>'.encode('utf-8')
        return out

    expected = letters_to_fake_urls(data.encode('utf-8'))
    new_file = FileTransform(orig_file, letters_to_fake_urls)
    transformed_data = new_file.open('rb').read()
    assert transformed_data == expected

