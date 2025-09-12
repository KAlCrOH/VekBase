from app.core import retrieval


def test_retrieval_keyword():
    files = retrieval.list_context_files()
    if not files:
        return  # skip silently if docs missing
    res = retrieval.retrieve('projekt')  # german word likely in charter
    assert isinstance(res, list)
    if res:
        assert 'file' in res[0]