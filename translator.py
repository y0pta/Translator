import requests
from bs4 import BeautifulSoup
import argparse


def url_join(base, new):
    if not base.endswith('/'):
        base += '/'
    return base + new


class WordNotFound(Exception):
    def __init__(self, word):
        self.word = word
        self.message = f"Sorry, unable to find {word}"
        super().__init__(self.message)


class ParseExampleException(Exception):
    def __init__(self, src_lang, dst_lang, num_src, num_dst):
        self.message = f"Number of examples in {src_lang} and {dst_lang} are not equal ({num_src} != {num_dst}).\n" \
                       f"Check HTML markup."
        super().__init__(self.message)


class UnsupportedLanguage(Exception):
    def __init__(self, lang):
        self.lang = lang
        self.message = f"Sorry, the program doesn't support {lang}"
        super().__init__(self.message)


class Translation:
    def __init__(self, src_lang: str, dst_lang: str, src_word: str,
                 translations: list, examples: list):
        self.src_lang = src_lang
        self.dst_lang = dst_lang.capitalize()
        self.word = src_word
        self.translations = translations
        self.usage_examples = examples

    def __str__(self):
        output = [
            f"{self.dst_lang} Translations:",
            self.translations[0],
            '\n',
            f"{self.dst_lang} Examples:",
            self.usage_examples[0],
            self.usage_examples[1],
            '\n\n'
        ]
        return "\n".join(output)


class Translator:
    URL = "https://context.reverso.net/translation"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/106.0.0.0 Safari/537.36'}
    langs = ['arabic',
             'German',
             'English',
             'Spanish',
             'French',
             'Hebrew',
             'Japanese',
             'Dutch',
             'Polish',
             'Portuguese',
             'Romanian',
             'Russian',
             'Turkish']

    def __init__(self):
        self.src_lang = None
        self.current_dst_lang = None
        self.word = None

    def translate(self, src_lang, trg_lang, word, file="") -> list:
        self.word = word

        # Firstly, check all language support
        trg_langs = []
        if trg_lang == 'all':
            trg_langs = [Translator.langs[i].lower() for i in range(0, len(Translator.langs)) if
                         Translator.langs[i].lower() != src_lang]
        else:
            trg_langs = [trg_lang]

        for lang in trg_langs + [src_lang]:
            if not Translator.check_language_support(lang):
                raise UnsupportedLanguage(lang)

        output = []
        # Make request and translate
        for trg_lang in trg_langs:
            self.current_dst_lang = trg_lang

            response = self._get_word_page(src_lang, trg_lang, word)
            soup = BeautifulSoup(response, 'html.parser')

            translations = self.find_all_translations(soup)
            examples = self.find_all_examples(soup)

            output.append(Translation(src_lang, trg_lang, word, translations, examples))

        return output

    @staticmethod
    def _get_word_page(src_lang: str, trg_lang: str, word: str) -> bytes:
        # make a request line
        get_request = url_join(Translator.URL, src_lang.lower() + '-' + trg_lang.lower())
        get_request = url_join(get_request, word)

        # make request
        i = 0
        for i in range(20):
            r = requests.get(get_request, headers=Translator.headers)
            if r.status_code == 200:
                return r.content
            elif r.status_code == 404:
                raise WordNotFound(word)

        if i == 19:
            raise ConnectionError("Something wrong with your internet connection.")

    @staticmethod
    def check_language_support(lang: str) -> bool:
        return lang.lower() in [x.lower() for x in Translator.langs]

    def _find(self, page_content, tag, attrib_entry):
        result = []
        for translation in page_content.find_all(tag, attrib_entry):
            result.append(translation.text)
        return result

    def find_all_translations(self, page_content: BeautifulSoup) -> list:
        return self._find(page_content, 'span', 'display-term')

    def find_all_examples(self, page_content: BeautifulSoup) -> list:
        examples = []
        examples_src = self._find(page_content, 'div', 'src ltr')
        examples_trg = self._find(page_content, 'div', 'trg')
        # if len(examples_trg) != len(examples_src):
        #    raise ParseExampleException(self.src_lang, self.current_dst_lang, len(examples_trg), len(examples_src))

        for i, example in enumerate(examples_src):
            examples.append(example.strip())
            examples.append(examples_trg[i].strip())
            examples.append("\n")

        return examples


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(
        description="Multilingual translator. Usage: > python translator.py <src_language> <dst_language> <word>")
    argparser.add_argument("src_lang", help="Source language", type=str)
    argparser.add_argument("dst_lang", help="Language to translate to", type=str)
    argparser.add_argument("word", help="Single word to translate", type=str)
    args = argparser.parse_args()

    t = Translator()
    try:
        translations = t.translate(args.src_lang, args.dst_lang, args.word, f"{args.word}.txt")
        output = ""
        for translation in translations:
            output = output + translation.__str__()

        print(output)
        with open(f"{args.word}.txt", 'w') as f:
            f.write(output)

    except BaseException as e:
        print(str(e))
