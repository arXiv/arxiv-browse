"""Tests browse.stream.tarstream."""
import io
import tarfile
from typing import List

from arxiv.files import MockStringFileObj
from browse.stream.tarstream import tar_stream_gen


def test_basic_tar_stream():
    # from https://www.cl.cam.ac.uk/~mgk25/ucs/examples/UTF-8-test.txt
    data = """
1  Some correct UTF-8 text                                                    |
                                                                              |
You should see the Greek word 'kosme':       "κόσμε"                          |
                                                                              |
2  Boundary condition test cases                                              |
                                                                              |
2.1  First possible sequence of a certain length                              |
                                                                              |
2.1.1  1 byte  (U-00000000):        "�"
2.1.2  2 bytes (U-00000080):        ""                                       |
2.1.3  3 bytes (U-00000800):        "ࠀ"                                       |
2.1.4  4 bytes (U-00010000):        "𐀀"                                       |
2.1.5  5 bytes (U-00200000):        "�����"                                       |
2.1.6  6 bytes (U-04000000):        "������"                                       |
                                                                              |
2.2  Last possible sequence of a certain length                               |
                                                                              |
2.2.1  1 byte  (U-0000007F):        ""
2.2.2  2 bytes (U-000007FF):        "߿"                                       |
2.2.3  3 bytes (U-0000FFFF):        "￿"                                       |
2.2.4  4 bytes (U-001FFFFF):        "����"                                       |
2.2.5  5 bytes (U-03FFFFFF):        "�����"                                       |
2.2.6  6 bytes (U-7FFFFFFF):        "������"                                       |
                                                                              |
2.3  Other boundary conditions                                                |
                                                                              |
2.3.1  U-0000D7FF = ed 9f bf = "퟿"                                            |
2.3.2  U-0000E000 = ee 80 80 = ""                                            |
2.3.3  U-0000FFFD = ef bf bd = "�"                                            |
2.3.4  U-0010FFFF = f4 8f bf bf = "􏿿"                                         |
2.3.5  U-00110000 = f4 90 80 80 = "����"                                         |"""

    fileobj = MockStringFileObj("fakefileobj.txt", data)
    tarinfo = tarfile.TarInfo(fileobj.name)
    tarinfo.mtime = 0
    tarinfo.size = fileobj.size

    tarstream = tar_stream_gen([fileobj])

    data_tar = b""
    count = 0
    for chunk in tarstream:
        data_tar += chunk
        count += 1

    assert count > 0
    assert data_tar

    result_tar = tarfile.open(fileobj=io.BytesIO(data_tar))
    members: List[tarfile.TarInfo] = []
    member_data: List[str] = []
    for member in result_tar.getmembers():
        members.append(member)
        member_data.append(result_tar.extractfile(member).read().decode("utf-8"))

    assert members
    assert members[0].name == fileobj.name
    assert members[0].size == fileobj.size
    assert member_data
    assert type(member_data[0]) == str and member_data[0] == data
