import typing

T = typing.TypeVar("T")


def chunks(data: typing.Iterable[T], batch_size=100) -> typing.Generator[typing.List[T], None, None]:
    """Yield successive batch_size-sized chunks from data."""

    batch = []
    for item in data:
        batch.append(item)
        if len(batch) == batch_size:
            yield batch
            batch = []

    if batch:
        yield batch
