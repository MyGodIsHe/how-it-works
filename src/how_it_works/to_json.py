def render(data: dict[str, list[str]]) -> None:
    print('{')
    for i, (k, v) in enumerate(data.items()):
        items = ','.join(f'"{n}"' for n in v)
        sep = ','
        if i == len(data) - 1:
            sep = ''
        print(f'"{k}":[{items}]', end=sep)
    print('}')
