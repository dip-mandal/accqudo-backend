def remove_duplicates(items, key):

    seen = set()

    result = []

    for item in items:

        value = item.get(key)

        if value and value not in seen:

            seen.add(value)

            result.append(item)

    return result