
__all__ = ['extract', 'extract_currency', 'extract_emoji',
           'extract_exclamations', 'extract_hashtags',
           'extract_intense_words', 'extract_mentions',
           'extract_questions', 'extract_words', 'extract_urls'
           ]

import re
from unicodedata import name
from collections import Counter
from urllib.parse import urlparse
from .emoji import EMOJI, EMOJI_ENTRIES
from .regex import (MENTION, HASHTAG, CURRENCY, CURRENCY_RAW, EXCLAMATION,
                    EXCLAMATION_MARK, QUESTION, QUESTION_MARK, URL)


def extract(text_list, regex, key_name, extracted=None, **kwargs):
    """Return a summary dictionary about arbitrary matches in ``text_list``.

    This function is used by other specialized functions to extract
    certain elements (hashtags, mentions, emojis, etc.).
    It can be used for other arbitrary elements/matches. You only need to
    provide your own regex.

    :param text_list: Any list of strings (social posts, page titles, etc.)
    :param regex: The regex pattern to use for extraction.
    :param key_name: The name of the object extracted in singular form
        (hashtag, mention, etc.)
    :param extracted: List of lists, optional. If the regex is not
        straightforward, and matches need to be made with special code,
        provide the extracted words/matches as a list for each element
        of ``text_list``.
    :param kwargs: Other kwargs that might be needed.
    :return summary: A dictionary summarizing the extracted data.
    """
    if isinstance(regex, str):
        regex = re.compile(regex)
    if isinstance(text_list, str):
        text_list = [text_list]
    if not extracted:
        extracted = [regex.findall(text.lower())
                     for text in text_list]
    flat = [item for sublist in extracted for item in sublist]

    summary = {
        key_name + 's': extracted,
        key_name + 's' + '_flat': flat,
        key_name + '_counts': [len(x) for x in extracted],
        key_name + '_freq': sorted(Counter([len(i)
                                            for i in extracted]).items(),
                                   key=lambda x: x[0]),
        'top_' + key_name + 's': sorted(Counter(flat).items(),
                                        key=lambda x: x[1],
                                        reverse=True),
        'overview': {
            'num_posts': len(text_list),
            'num_' + key_name + 's': len(flat),
            key_name + 's' + '_per_post': len(flat) / len(text_list),
            'unique_' + key_name + 's': len(set(flat)),
        }
    }
    return summary


def extract_currency(text_list, left_chars=20, right_chars=20):
    """Return a summary dictionary about currency symbols in ``text_list``

    Get a summary of the number of currency symbols, their frequency,
    the top ones, and more.

    :param text_list: A list of text strings.
    :param left_chars: The number of characters to extract, to the
        left of the symbol when getting ``surrounding_text``
    :param right_chars: The number of characters to extract, to the
        left of the symbol when getting ``surrounding_text``
    :returns summary: A dictionary with various stats about currencies

    >>> posts = ['today ₿1 is around $4k', 'and ₿ in £ & €?', 'no idea']
    >>> currency_summary = extract_currency(posts)
    >>> currency_summary.keys()
    dict_keys(['currency_symbols', 'currency_symbols_flat',
    'currency_symbol_counts', 'currency_symbol_freq',
    'top_currency_symbols', 'overview', 'currency_symbol_names'])

    >>> currency_summary['currency_symbols']
    [['₿', '$'], ['₿', '£', '€'], []]

    A simple extract of currencies from each of the posts. An empty list if
    none exist

    >>> currency_summary['currency_symbols_flat']
    ['₿', '$', '₿', '£', '€']

    All currency symbols in one flat list.

    >>> currency_summary['currency_symbol_counts']
    [2, 3, 0]

    The count of currency symbols per post.

    >>> currency_summary['currency_symbol_freq']
    [(0, 1), (2, 1), (3, 1)]

    Shows how many posts had 0, 1, 2, 3, etc. currency symbols
    (number_of_symbols, count)

    >>> currency_summary['top_currency_symbols']
    [('₿', 2), ('$', 1), ('£', 1), ('€', 1)]

    >>> currency_summary['currency_symbol_names']
    [['bitcoin sign', 'dollar sign'], ['bitcoin sign', 'pound sign',
    'euro sign'], []]

    >>> currency_summary['surrounding_text']
    [['today ₿1 is around $4k'], ['and ₿ in £ & €?'], []]

    >>> extract_currency(posts, 5, 5)['surrounding_text']
    [['oday ₿1 is ', 'ound $4k'], ['and ₿ in £', ' & €?'], []]

    >>> extract_currency(posts, 0, 3)['surrounding_text']
    [['₿1 i', '$4k'], ['₿ in', '£ & ', '€?'], []]

    >>> currency_summary['overview']
    {'num_posts': 3,
    'num_currency_symbols': 5,
    'currency_symbols_per_post': 1.6666666666666667,
    'unique_currency_symbols': 4}
    """
    summary = extract(text_list, CURRENCY, 'currency_symbol')
    summary['currency_symbol_names'] = [[name(c).lower() for c in x] if x
                                        else [] for x in
                                        summary['currency_symbols']]
    surrounding_text_regex = re.compile(r'.{0,' + str(left_chars) + '}' +
                                        CURRENCY_RAW +
                                        r'.{0,' + str(right_chars) + '}')
    summary['surrounding_text'] = [surrounding_text_regex.findall(text)
                                   for text in text_list]
    return summary


def extract_emoji(text_list):
    """Return a summary dictionary about emoji in ``text_list``

    Get a summary of the number of emoji, their frequency, the top
    ones, and more.

    :param text_list: A list of text strings.
    :returns summary: A dictionary with various stats about emoji

    >>> posts = ['I am grinning 😀','A grinning cat 😺',
    ...          'hello! 😀😀😀 💛💛', 'Just text']

    >>> emoji_summary = extract_emoji(posts)
    >>> emoji_summary.keys()
    dict_keys(['emoji', 'emoji_text', 'emoji_flat', 'emoji_flat_text',
    'emoji_counts', 'emoji_freq', 'top_emoji', 'top_emoji_text',
    'top_emoji_groups', 'top_emoji_sub_groups', 'overview'])


    >>> emoji_summary['emoji']
    [['😀'], ['😺'], ['😀', '😀', '😀', '💛', '💛'], []]

    >>> emoji_summary['emoji_text']
    [['grinning face'], ['grinning cat'], ['grinning face', 'grinning face',
      'grinning face', 'yellow heart', 'yellow heart'], []]

    A simple extract of emoji from each of the posts. An empty
    list if none exist

    >>> emoji_summary['emoji_flat']
    ['😀', '😺', '😀', '😀', '😀', '💛', '💛']

    >>> emoji_summary['emoji_flat_text']
    ['grinning face', 'grinning cat', 'grinning face', 'grinning face',
    'grinning face', 'yellow heart', 'yellow heart']

    All emoji in one flat list.

    >>> emoji_summary['emoji_counts']
    [1, 1, 5, 0]

    The count of emoji per post.

    >>> emoji_summary['emoji_freq']
    [(0, 1), (1, 2), (5, 1)]

    Shows how many posts had 0, 1, 2, 3, etc. emoji
    (number_of_emoji, count)

    >>> emoji_summary['top_emoji']
    [('😀', 4), ('💛', 2), ('😺', 1)]

    >>> emoji_summary['top_emoji_text']
    [('grinning face', 4), ('yellow heart', 2),
     ('grinning cat', 1)]

    >>> emoji_summary['top_emoji_groups']
    [('Smileys & Emotion', 7)]

    >>> emoji_summary['top_emoji_sub_groups']
    [('face-smiling', 4), ('emotion', 2), ('cat-face', 1)]

    >>> emoji_summary['overview']
    {'num_posts': 4,
     'num_emoji': 7,
     'emoji_per_post': 1.75,
     'unique_emoji': 3}
    """
    emoji = [re.findall(EMOJI, text.lower()) for text in text_list]
    emoji_flat = [item for sublist in emoji for item in sublist]
    emoji_flat_text = [EMOJI_ENTRIES[em].name for em in emoji_flat]
    emoji_groups = [EMOJI_ENTRIES[em].group for em in emoji_flat]
    emoji_sub_groups = [EMOJI_ENTRIES[em].sub_group for em in emoji_flat]
    summary = {
        'emoji': emoji,
        'emoji_text': [[EMOJI_ENTRIES[em].name for em in em_list]
                       for em_list in emoji],
        'emoji_flat': emoji_flat,
        'emoji_flat_text': emoji_flat_text,
        'emoji_counts': [len(em) for em in emoji],
        'emoji_freq': sorted(Counter([len(em) for em in emoji]).items(),
                             key=lambda x: x[0]),
        'top_emoji': sorted(Counter(emoji_flat).items(),
                            key=lambda x: x[1],
                            reverse=True),
        'top_emoji_text': sorted(Counter(emoji_flat_text).items(),
                                 key=lambda x: x[1],
                                 reverse=True),
        'top_emoji_groups': sorted(Counter(emoji_groups).items(),
                                   key=lambda x: x[1],
                                   reverse=True),
        'top_emoji_sub_groups': sorted(Counter(emoji_sub_groups).items(),
                                       key=lambda x: x[1],
                                       reverse=True),
        'overview': {
            'num_posts': len(text_list),
            'num_emoji': len(emoji_flat),
            'emoji_per_post': len(emoji_flat) / len(text_list),
            'unique_emoji': len(set(emoji_flat)),
        }

    }
    return summary


def extract_exclamations(text_list):
    """Return a summary dictionary about exclamation (mark)s in ``text_list``

    Get a summary of the number of exclamation marks, their frequency,
    the top ones, as well the exclamations written/said.

    :param text_list: A list of text strings.
    :returns summary: A dictionary with various stats about exclamations

    >>> posts = ['Who are you!', 'What is this!', 'No exclamation here?']
    >>> exclamation_summary = extract_exclamations(posts)
    >>> exclamation_summary.keys()
    dict_keys(['exclamation_marks', 'exclamation_marks_flat',
    'exclamation_mark_counts', 'exclamation_mark_freq',
    'top_exclamation_marks', 'overview', 'exclamation_mark_names',
    'exclamation_text'])

    >>> exclamation_summary['exclamation_marks']
    [['!'], ['!'], []]

    A simple extract of exclamation marks from each of the posts. An empty
    list if none exist

    >>> exclamation_summary['exclamation_marks_flat']
    ['!', '!']

    All exclamation marks in one flat list.

    >>> exclamation_summary['exclamation_mark_counts']
    [1, 1, 0]

    The count of exclamation marks per post.

    >>> exclamation_summary['exclamation_mark_freq']
    [(0, 1), (1, 2)]

    Shows how many posts had 0, 1, 2, 3, etc. exclamation marks
    (number_of_symbols, count)

    >>> exclamation_summary['top_exclamation_marks']
    [('!', 2)]

    Might be interesting if you have different types of exclamation marks

    >>> exclamation_summary['exclamation_mark_names']
    [['exclamation mark'], ['exclamation mark'], []]

    >>> exclamation_summary['overview']
    {'num_posts': 3,
    'num_exclamation_marks': 2,
    'exclamation_marks_per_post': 0.6666666666666666,
    'unique_exclamation_marks': 1}

    >>> posts2 = ["don't go there!", 'مرحبا. لا تذهب!', '¡Hola! ¿cómo estás?',
    ... 'a few different exclamation marks! make sure you see them!']

    >>> exclamation_summary = extract_exclamations(posts2)

    >>> exclamation_summary['exclamation_marks']
    [['!'], ['!'], ['¡', '!'], ['!', '!']]
    # might be displayed in opposite order due to RTL exclamation mark
    A simple extract of exclamation marks from each of the posts.
    An empty list if none exist

    >>> exclamation_summary['exclamation_marks_flat']
    ['!', '!', '¡', '!', '!', '!']

    All exclamation marks in one flat list.

    >>> exclamation_summary['exclamation_mark_counts']
    [1, 1, 2, 2]

    The count of exclamation marks per post.

    >>> exclamation_summary['exclamation_mark_freq']
    [(1, 2), (2, 2)]

    Shows how many posts had 0, 1, 2, 3, etc. exclamation marks
    (number_of_symbols, count)

    >>> exclamation_summary['top_exclamation_marks']
    [('!', 5), ('¡', 1)]

    Might be interesting if you have different types of exclamation marks

    >>> exclamation_summary['exclamation_mark_names']
    [['exclamation mark'], ['exclamation mark'],
    ['inverted exclamation mark', 'exclamation mark'],
    ['exclamation mark', 'exclamation mark']]

    >>> exclamation_summary['overview']
    {'num_posts': 4,
    'num_exclamation_marks': 6,
    'exclamation_marks_per_post': 1.5,
    'unique_exclamation_marks': 4}
    """
    summary = extract(text_list, EXCLAMATION_MARK, key_name='exclamation_mark')
    summary['exclamation_mark_names'] = [[name(c).lower() for c in x] if x
                                         else [] for x in
                                         summary['exclamation_marks']]
    summary['exclamation_text'] = [EXCLAMATION.findall(text)
                                   for text in text_list]
    return summary


def extract_hashtags(text_list):
    """Return a summary dictionary about hashtags in ``text_list``

    Get a summary of the number of hashtags, their frequency, the top
    ones, and more.

    :param text_list: A list of text strings.
    :returns summary: A dictionary with various stats about hashtags

    >>> posts = ['i like #blue', 'i like #green and #blue', 'i like all']
    >>> hashtag_summary = extract_hashtags(posts)
    >>> hashtag_summary.keys()
    dict_keys(['hashtags', 'hashtags_flat', 'hashtag_counts', 'hashtag_freq',
    'top_hashtags', 'overview'])

    >>> hashtag_summary['hashtags']
    [['#blue'], ['#green', '#blue'], []]

    A simple extract of hashtags from each of the posts. An empty list if
    none exist

    >>> hashtag_summary['hashtags_flat']
    ['#blue', '#green', '#blue']

    All hashtags in one flat list.

    >>> hashtag_summary['hashtag_counts']
    [1, 2, 0]

    The count of hashtags per post.

    >>> hashtag_summary['hashtag_freq']
    [(0, 1), (1, 1), (2, 1)]

    Shows how many posts had 0, 1, 2, 3, etc. hashtags
    (number_of_hashtags, count)

    >>> hashtag_summary['top_hashtags']
    [('#blue', 2), ('#green', 1)]

    >>> hashtag_summary['overview']
    {'num_posts': 3,
     'num_hashtags': 3,
     'hashtags_per_post': 1.0,
     'unique_hashtags': 2}
     """
    return extract(text_list, HASHTAG, 'hashtag')


def extract_intense_words(text_list, min_reps=3):
    regex = re.compile(r'(\S*)(\S)({}\S*)'.format((min_reps - 1) * r'\2'))
    extracted = [[''.join(x) for x in regex.findall(text)]
                 for text in text_list]

    return extract(text_list, regex, 'intense_word', extracted)


def extract_mentions(text_list):
    """Return a summary dictionary about mentions in ``text_list``

    Get a summary of the number of mentions, their frequency, the top
    ones, and more.

    :param text_list: A list of text strings.
    :returns summary: A dictionary with various stats about mentions

    >>> posts = ['hello @john and @jenny', 'hi there @john', 'good morning']
    >>> mention_summary = extract_mentions(posts)
    >>> mention_summary.keys()
    dict_keys(['mentions', 'mentions_flat', 'mention_counts', 'mention_freq',
    'top_mentions', 'overview'])

    >>> mention_summary['mentions']
    [['@john', '@jenny'], ['@john'], []]

    A simple extract of mentions from each of the posts. An empty list if
    none exist

    >>> mention_summary['mentions_flat']
    ['@john', '@jenny', '@john']

    All mentions in one flat list.

    >>> mention_summary['mention_counts']
    [2, 1, 0]

    The count of mentions per post.

    >>> mention_summary['mention_freq']
    [(0, 1), (1, 1), (2, 1)]

    Shows how many posts had 0, 1, 2, 3, etc. mentions
    (number_of_mentions, count)

    >>> mention_summary['top_mentions']
    [('@john', 2), ('@jenny', 1)]

    >>> mention_summary['overview']
    {'num_posts': 3, # number of posts
     'num_mentions': 3,
     'mentions_per_post': 1.0,
     'unique_mentions': 2}
    """
    return extract(text_list, MENTION, 'mention')


def extract_questions(text_list):
    """Return a summary dictionary about question(mark)s in ``text_list``

    Get a summary of the number of question marks, their frequency,
    the top ones, as well the questions asked.

    :param text_list: A list of text strings.
    :returns summary: A dictionary with various stats about questions

    >>> posts = ['How are you?', 'What is this?', 'No question Here!']
    >>> question_summary = extract_questions(posts)
    >>> question_summary.keys()
    dict_keys(['question_marks', 'question_marks_flat',
    'question_mark_counts', 'question_mark_freq', 'top_question_marks',
    'overview', 'question_mark_names', 'question_text'])

    >>> question_summary['question_marks']
    [['?'], ['?'], []]

    A simple extract of question marks from each of the posts. An empty
    list if none exist

    >>> question_summary['question_marks_flat']
    ['?', '?']

    All question marks in one flat list.

    >>> question_summary['question_mark_counts']
    [1, 1, 0]

    The count of question marks per post.

    >>> question_summary['question_mark_freq']
    [(0, 1), (1, 2)]

    Shows how many posts had 0, 1, 2, 3, etc. question marks
    (number_of_symbols, count)

    >>> question_summary['top_question_marks']
    [('?', 2)]

    Might be interesting if you have different types of question marks
    (Arabic, Spanish, Greek, Armenian, or other)

    >>> question_summary['question_mark_names']
    [['question mark'], ['question mark'], []]

    >>> question_summary['overview']
    {'num_posts': 3,
    'num_question_marks': 2,
    'question_marks_per_post': 0.6666666666666666,
    'unique_question_marks': 1}

    >>> posts2 = ['Πώς είσαι;', 'مرحباً. كيف حالك؟', 'Hola, ¿cómo estás?',
    ... 'Can you see the new questions? Did you notice the different marks?']

    >>> question_summary = extract_questions(posts2)

    >>> question_summary['question_marks']
    [[';'], ['؟'], ['¿', '?'], ['?', '?']]
    # might be displayed in opposite order due to RTL question mark
    A simple extract of question marks from each of the posts. An empty list if
    none exist

    >>> question_summary['question_marks_flat']
    [';', '؟', '¿', '?', '?', '?']

    All question marks in one flat list.

    >>> question_summary['question_mark_counts']
    [1, 1, 2, 2]

    The count of question marks per post.

    >>> question_summary['question_mark_freq']
    [(1, 2), (2, 2)]

    Shows how many posts had 0, 1, 2, 3, etc. question marks
    (number_of_symbols, count)

    >>> question_summary['top_question_marks']
    [('?', 3), (';', 1), ('؟', 1), ('¿', 1)]

    Might be interesting if you have different types of question marks
    (Arabic, Spanish, Greek, Armenian, or other)

    >>> question_summary['question_mark_names']
    [['greek question mark'], ['arabic question mark'],
    ['inverted question mark', 'question mark'],
    ['question mark', 'question mark']]
    # correct order

    >>> question_summary['overview']
    {'num_posts': 4,
    'num_question_marks': 6,
    'question_marks_per_post': 1.5,
    'unique_question_marks': 4}
    """
    summary = extract(text_list, QUESTION_MARK, key_name='question_mark')
    summary['question_mark_names'] = [[name(c).lower() for c in x] if x
                                      else [] for x in
                                      summary['question_marks']]
    summary['question_text'] = [QUESTION.findall(text)
                                for text in text_list]
    return summary


def extract_urls(text_list):
    """Return a summary dictionary about URLs in ``text_list``

    Get a summary of the number of URLs, their frequency, the top
    ones, and more.
    This does NOT validate URLs, www.a.b would count as a URL

    :param text_list: A list of text strings.
    :returns summary: A dictionary with various stats about URLs

    >>> posts = ['one link http://example.com', 'two: http://a.com www.b.com',
    ...          'no links here',
    ...          'long url http://example.com/one/two/?1=one&2=two']
    >>> url_summary = extract_urls(posts)
    >>> url_summary.keys()
    dict_keys(['urls', 'urls_flat', 'url_counts', 'url_freq',
    'top_urls', 'overview', 'top_domains', 'top_tlds'])

    >>> url_summary['urls']
    [['http://example.com'],
     ['http://a.com', 'http://www.b.com'],
     [],
     ['http://example.com/one/two/?1=one&2=two']]

    A simple extract of urls from each of the posts. An empty list if
    none exist

    >>> url_summary['urls_flat']
    ['http://example.com', 'http://a.com', 'http://www.b.com',
     'http://example.com/one/two/?1=one&2=two']

    All urls in one flat list.

    >>> url_summary['url_counts']
    [1, 2, 0, 1]

    The count of urls per post.

    >>> url_summary['url_freq']
    [(0, 1), (1, 2), (2, 1)]

    Shows how many posts had 0, 1, 2, 3, etc. urls
    (number_of_urls, count)

    >>> url_summary['top_urls']
    [('http://example.com', 1), ('http://a.com', 1), ('http://www.b.com', 1),
     ('http://example.com/one/two/?1=one&2=two', 1)]

    >>> url_summary['top_domains']
    [('example.com', 2), ('a.com', 1), ('www.b.com', 1)]

    >>> url_summary['top_tlds']
    [('com', 4)]

    >>> url_summary['overview']
    {'num_posts': 4,
     'num_urls': 4,
     'urls_per_post': 1.0,
     'unique_urls': 4}
     """
    extracted = [URL.findall(x) for x in text_list]
    for urllist in extracted:
        for i, url in enumerate(urllist):
            if url.lower().startswith('www') or url.lower().startswith('ftp'):
                urllist[i] = 'http://' + url
    domains = [[urlparse(u).netloc for u in e] for e in extracted]
    domains_flat = [item for sublist in domains for item in sublist]
    top_domains = sorted(Counter(domains_flat).items(),
                         key=lambda x: x[1], reverse=True)
    tlds = [[d.split('.')[-1] for d in dom] for dom in domains]
    tlds_flat = [item for sublist in tlds for item in sublist]
    top_tlds = sorted(Counter(tlds_flat).items(),
                      key=lambda x: x[1], reverse=True)
    summary = extract(text_list, URL, 'url', extracted)
    summary['top_domains'] = top_domains
    summary['top_tlds'] = top_tlds
    return summary


def extract_words(text_list, words_to_extract, entire_words_only=False):
    """Return a summary dictionary about ``words_to_extract`` in ``text_list``.

    Get a summary of the number of words, their frequency, the top
    ones, and more.

    :param text_list: A list of text strings.
    :param words_to_extract: A list of words to extract from ``text_list``.
    :param entire_words_only: Whether or not to find only complete words
        (as specified by ``words_to_find``) or find any any of the
        words as part of longer strings.
    :returns summary: A dictionary with various stats about the words

    >>> posts = ['there is rain, it is raining', 'there is snow and rain',
                 'there is no rain, it is snowing', 'there is nothing']
    >>> word_summary = extract_words(posts, ['rain', 'snow'], True)
    >>> word_summary.keys()
    dict_keys(['words', 'words_flat', 'word_counts', 'word_freq',
    'top_words', 'overview'])

    >>> word_summary['overview']
    {'num_posts': 4,
     'num_words': 4,
     'words_per_post': 1,
     'unique_words': 2}

    >>> word_summary['words']
    [['rain'], ['snow', 'rain'], ['rain'], []]

    A simple extract of mentions from each of the posts. An empty list if
    none exist

    >>> word_summary['words_flat']
    ['rain', 'snow', 'rain', 'rain']

    All mentions in one flat list.

    >>> word_summary['word_counts']
    [1, 2, 1, 0]

    The count of mentions for each post.

    >>> word_summary['word_freq']
    [(0, 1) (1, 2), (2, 1)]

    Shows how many posts had 0, 1, 2, 3, etc. words
    (number_of_words, count)

    >>> word_summary['top_words']
    [('rain', 3), ('snow', 1)]

    Check the same posts extracting any occurrence of the specified words
    with ``entire_words_only=False``:

    >>> word_summary = extract_words(posts, ['rain', 'snow'], False)

    >>> word_summary['overview']
    {'num_posts': 4, # number of posts
     'num_words': 6,
     'words_per_post': 1.5,
     'unique_words': 4}

    >>> word_summary['words']
    [['rain', 'raining'], ['snow', 'rain'], ['rain', 'snowing'], []]

    Note that the extracted words are the complete words so you can see
    where they occurred. In case "training" was mentioned,
    you would see that it is not related to rain for example.

    >>> word_summary['words_flat']
    ['rain', 'raining', 'snow', 'rain', 'rain', 'snowing']

    All mentions in one flat list.

    >>> word_summary['word_counts']
    [2, 2, 2, 0]

    >>> word_summary['word_freq']
    [(0, 1), (2, 3)]

    Shows how many posts had 0, 1, 2, 3, etc. words
    (number_of_words, count)

    >>> word_summary['top_words']
    [('rain', 3), ('raining', 1), ('snow', 1), ('snowing', 1)]
    """
    if isinstance(words_to_extract, str):
        words_to_extract = [words_to_extract]

    text_list = [text.lower() for text in text_list]
    words_to_extract = [word.lower() for word in words_to_extract]

    if entire_words_only:
        regex = [r'\b' + x + r'\b' for x in words_to_extract]
        word_regex = re.compile(r'|'.join(regex), re.IGNORECASE)
    else:
        regex = [r'\S*' + x + r'\S*' for x in words_to_extract]
        word_regex = re.compile('|'.join(regex), re.IGNORECASE)

    return extract(text_list, word_regex, 'word')
