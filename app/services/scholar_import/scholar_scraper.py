from scholarly import scholarly


def get_scholar_profile(user_id):

    author = scholarly.search_author_id(user_id)

    author = scholarly.fill(author)

    return author