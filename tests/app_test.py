from unittest import TestCase
import datamodel
import app
import re
import jinja2

__author__ = 'qingye3'


class TestApp(TestCase):
    def cannot_find_word(self, query_word, query_text):
        regex = re.compile(r'\b%s\b' % query_word)
        return not regex.match(query_text)

    def cannot_find(self, query_match, query_text):
        regex = re.compile(r'%s' % query_match)
        return not regex.match(query_text)

    def test_good_comment(self):
        app.submit_comment("some_lonely_author", "some_comment")
        comment = datamodel.Comment.query.filter_by(author="some_lonely_author").first()
        self.assertEqual(comment.content, "some_comment")
        datamodel.db.session.delete(comment)
        datamodel.db.session.commit()

    def test_red_words(self):
        app.submit_comment("some_lonely_author", "Fuck, you deserve to die.")
        comment = datamodel.Comment.query.filter_by(author="some_lonely_author").first()
        self.assertTrue(self.cannot_find_word("Fuck", comment.content))
        self.assertTrue(self.cannot_find_word("die", comment.content))
        datamodel.db.session.delete(comment)
        datamodel.db.session.commit()

    def test_SQL_injection(self):
        app.submit_comment("some_lonely_author", "; DROP TABLE comments;")
        comment = datamodel.Comment.query.filter_by(author="some_lonely_author").first()
        datamodel.db.session.delete(comment)
        datamodel.db.session.commit()

    def test_XSS(self):
        app.submit_comment("some_lonely_author", '</p> <a href="some_dummy_url"> stuff </a> <p>')
        comment = datamodel.Comment.query.filter_by(author="some_lonely_author").first()
        rendered = str(jinja2.utils.escape(comment.content))
        self.assertTrue(self.cannot_find('</textarea>', rendered))
        self.assertTrue(self.cannot_find('<a href', rendered))
        datamodel.db.session.delete(comment)
        datamodel.db.session.commit()
