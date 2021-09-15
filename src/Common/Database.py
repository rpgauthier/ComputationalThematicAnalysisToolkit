import logging
import sqlite3
import pandas as pd
from math import log

import Common.Constants as Constants

class DatabaseConnection():
    def __init__(self, current_workspace_path):
        self.__conn = sqlite3.connect(current_workspace_path+"\\workspace_sqlite3.db")
        self.__conn.execute("PRAGMA foreign_keys=ON")
    
    def __del__(self):
        self.__conn.close()

    def Create(self):
        logger = logging.getLogger(__name__+".Create")
        logger.info("Starting")
        try:
            c = self.__conn.cursor()

            sql_create_datasets_table = """ CREATE TABLE IF NOT EXISTS datasets (
                                                    id INTEGER PRIMARY KEY,
                                                    dataset_key TEXT UNIQUE,
                                                    token_type TEXT
                                                )"""
            c.execute(sql_create_datasets_table)

            sql_create_datasets_table = """ CREATE TABLE IF NOT EXISTS fields (
                                                    id INTEGER PRIMARY KEY,
                                                    dataset_id, INTEGER,
                                                    field_key TEXT,
                                                    position INT,
                                                    FOREIGN KEY(dataset_id) REFERENCES datasets(id)
                                                        ON UPDATE CASCADE
                                                        ON DELETE CASCADE,
                                                    UNIQUE(dataset_id, field_key)
                                                )"""
            c.execute(sql_create_datasets_table)

            sql_create_datasets_table = """ CREATE TABLE IF NOT EXISTS documents (
                                                    id INTEGER PRIMARY KEY,
                                                    dataset_id, INTEGER,
                                                    document_key TEXT,
                                                    FOREIGN KEY(dataset_id) REFERENCES datasets(id)
                                                        ON UPDATE CASCADE
                                                        ON DELETE CASCADE,
                                                    UNIQUE(dataset_id, document_key)
                                                )"""
            c.execute(sql_create_datasets_table)

            sql_create_stringtokens_table = """ CREATE TABLE IF NOT EXISTS string_tokens (
                                                    id integer PRIMARY KEY,
                                                    dataset_id INTEGER,
                                                    field_id INTEGER,
                                                    document_id INTEGER,
                                                    position INT,
                                                    text TEXT,
                                                    stem TEXT,
                                                    lemma TEXT,
                                                    pos TEXT,
                                                    spacy_stopword BOOLEAN,
                                                    text_tf FLOAT,
                                                    stem_tf FLOAT,
                                                    lemma_tf FLOAT,
                                                    text_idf FLOAT,
                                                    stem_idf FLOAT,
                                                    lemma_idf FLOAT,
                                                    text_tfidf FLOAT,
                                                    stem_tfidf FLOAT,
                                                    lemma_tfidf FLOAT,
                                                    included BOOLEAN DEFAULT 1,
                                                    FOREIGN KEY(dataset_id) REFERENCES datasets(id)
                                                        ON UPDATE CASCADE
                                                        ON DELETE CASCADE,
                                                    FOREIGN KEY(field_id) REFERENCES fields(id)
                                                        ON UPDATE CASCADE
                                                        ON DELETE CASCADE,
                                                    FOREIGN KEY(document_id) REFERENCES documents(id)
                                                        ON UPDATE CASCADE
                                                        ON DELETE CASCADE
                                                )"""
            c.execute(sql_create_stringtokens_table)

            sql_create_text_index = """CREATE INDEX string_tokens_text_index ON string_tokens(dataset_id, text, document_id)"""
            c.execute(sql_create_text_index)

            sql_create_stem_index = """CREATE INDEX string_tokens_stem_index ON string_tokens(dataset_id, stem, document_id)"""
            c.execute(sql_create_stem_index)

            sql_create_lemma_index = """CREATE INDEX string_tokens_lemma_index ON string_tokens(dataset_id, lemma, document_id)"""
            c.execute(sql_create_lemma_index)

            sql_create_stringtokensincluded_view = """ CREATE VIEW string_tokens_included_view (
                                                        dataset_id,
                                                        words,
                                                        pos,
                                                        num_of_words,
                                                        num_of_docs,
                                                        spacy_stopword,
                                                        tfidf_range
                                                        )
                                                        AS
                                                        SELECT
                                                            dataset_id,
                                                            CASE (SELECT datasets.token_type FROM datasets WHERE datasets.id = dataset_id)
                                                                WHEN 'stem' THEN stem
                                                                WHEN 'lemma' THEN lemma
                                                                ELSE text
                                                                END words,
                                                            pos,
                                                            COUNT(CASE (SELECT datasets.token_type FROM datasets WHERE datasets.id = dataset_id)
                                                                  WHEN 'stem' THEN stem
                                                                  WHEN 'lemma' THEN lemma
                                                                  ELSE text
                                                                  END),
                                                            COUNT(DISTINCT document_id),
                                                            spacy_stopword,
                                                            CASE (SELECT datasets.token_type FROM datasets WHERE datasets.id = dataset_id)
                                                                WHEN 'stem' THEN ROUND(MIN(stem_tfidf),4) ||' - '|| ROUND(MAX(stem_tfidf),4)
                                                                WHEN 'lemma' THEN ROUND(MIN(lemma_tfidf),4) ||' - '|| ROUND(MAX(lemma_tfidf),4)
                                                                ELSE ROUND(MIN(text_tfidf),4) ||' - '|| ROUND(MAX(text_tfidf),4)
                                                                END tfidf_range
                                                        FROM string_tokens
                                                        WHERE included = 1
                                                        GROUP BY dataset_id,
                                                                 CASE (SELECT datasets.token_type FROM datasets WHERE datasets.id = dataset_id)
                                                                    WHEN 'stem' THEN stem
                                                                    WHEN 'lemma' THEN lemma
                                                                    ELSE text
                                                                 END,
                                                                 pos, spacy_stopword
                                                        """
            c.execute(sql_create_stringtokensincluded_view)
            sql_create_stringtokensremoved_view = """ CREATE VIEW string_tokens_removed_view (
                                                        dataset_id,
                                                        words,
                                                        pos,
                                                        num_of_words,
                                                        num_of_docs,
                                                        spacy_stopword,
                                                        tfidf_range
                                                        )
                                                        AS
                                                        SELECT
                                                            dataset_id,
                                                            CASE (SELECT datasets.token_type FROM datasets WHERE datasets.id = dataset_id)
                                                                WHEN 'stem' THEN stem
                                                                WHEN 'lemma' THEN lemma
                                                                ELSE text
                                                                END words,
                                                            pos,
                                                            COUNT(CASE (SELECT datasets.token_type FROM datasets WHERE datasets.id = dataset_id)
                                                                  WHEN 'stem' THEN stem
                                                                  WHEN 'lemma' THEN lemma
                                                                  ELSE text
                                                                  END),
                                                            COUNT(DISTINCT document_id),
                                                            spacy_stopword,
                                                            CASE (SELECT datasets.token_type FROM datasets WHERE datasets.id = dataset_id)
                                                                WHEN 'stem' THEN ROUND(MIN(stem_tfidf),4) ||' - '|| ROUND(MAX(stem_tfidf),4)
                                                                WHEN 'lemma' THEN ROUND(MIN(lemma_tfidf),4) ||' - '|| ROUND(MAX(lemma_tfidf),4)
                                                                ELSE ROUND(MIN(text_tfidf),4) ||' - '|| ROUND(MAX(text_tfidf),4)
                                                                END tfidf_range
                                                        FROM string_tokens
                                                        WHERE included = 0
                                                        GROUP BY dataset_id,
                                                                 CASE (SELECT datasets.token_type FROM datasets WHERE datasets.id = dataset_id)
                                                                    WHEN 'stem' THEN stem
                                                                    WHEN 'lemma' THEN lemma
                                                                    ELSE text
                                                                 END,
                                                                 pos, spacy_stopword
                                                        """
            c.execute(sql_create_stringtokensremoved_view)

            self.__conn.commit()
            c.close()
        except sqlite3.Error:
            logger.exception("sql failed with sql error")
        logger.info("Finished")

    def InsertDataset(self, dataset_key, token_type):
        logger = logging.getLogger(__name__+".InsertDataset")
        logger.info("Starting")
        try:
            c = self.__conn.cursor()
            sql_insert_dataset = """INSERT INTO datasets (
                                        dataset_key,
                                        token_type
                                        ) values (?, ?)"""
            c.execute(sql_insert_dataset, (str(dataset_key), str(token_type),))
            self.__conn.commit()
            c.close()
        except sqlite3.Error as e:
            logger.exception("sql failed with error")
        logger.info("Finished")

    def UpdateDatasetKey(self, old_dataset_key, new_dataset_key):
        logger = logging.getLogger(__name__+".UpdateDatasetKey")
        logger.info("Starting")
        try:
            c = self.__conn.cursor()
            sql_update_datasetkey = """UPDATE datasets 
                                       SET dataset_key = ?
                                       WHERE dataset_key = ?
                                       """
            c.execute(sql_update_datasetkey, (str(old_dataset_key), str(new_dataset_key)))
            self.__conn.commit()

            c.close()
        except sqlite3.Error as e:
            logger.exception("sql failed with error")
        logger.info("Finished")

    def UpdateDatasetTokenType(self, dataset_key, token_type):
        logger = logging.getLogger(__name__+".UpdateDatasetTokenType")
        logger.info("Starting")
        try:
            c = self.__conn.cursor()
            sql_update_tokentype = """UPDATE datasets
                                      SET token_type = ?
                                      WHERE dataset_key = ?
                                      """
            c.execute(sql_update_tokentype, (token_type, str(dataset_key),))
            self.__conn.commit()
            c.close()
        except sqlite3.Error as e:
            logger.exception("sql failed with error")
        logger.info("Finished")

    def DeleteDataset(self, dataset_key):
        logger = logging.getLogger(__name__+".DeleteDataset")
        logger.info("Starting")
        try:
            c = self.__conn.cursor()
            sql_delete_dataset = """DELETE FROM datasets
                                    WHERE dataset_key = ?
                                    """
            c.execute(sql_delete_dataset, (str(dataset_key),))
            self.__conn.commit()
            c.close()
        except sqlite3.Error as e:
            logger.exception("sql failed with error")
        logger.info("Finished")
    
    def InsertField(self, dataset_key, field_key):
        logger = logging.getLogger(__name__+".InsertField")
        logger.info("Starting")
        try:
            c = self.__conn.cursor()
            sql_select_datasetid = """SELECT id
                                    FROM datasets 
                                    WHERE dataset_key = ?
                                    """
            c.execute(sql_select_datasetid, (str(dataset_key),))
            dataset_id = c.fetchone()[0]
            sql_insert_tokens = """INSERT INTO fields (
                                        dataset_id,
                                        field_key
                                        ) values (?, ?)"""
            c.execute(sql_insert_tokens, (dataset_id, str(field_key),))
            self.__conn.commit()
            c.close()
        except sqlite3.Error as e:
            logger.exception("sql failed with error")
        logger.info("Finished")
    
    def UpdateFieldPosition(self, dataset_key, field_key, position):
        logger = logging.getLogger(__name__+".InsertField")
        logger.info("Starting")
        try:
            c = self.__conn.cursor()
            sql_select_datasetid = """SELECT id
                                      FROM datasets 
                                      WHERE dataset_key = ?
                                      """
            c.execute(sql_select_datasetid, (str(dataset_key),))
            dataset_id = c.fetchone()[0]
            sql_update_fieldposition = """UPDATE fields
                                          SET position = ?
                                          WHERE dataset_id = ?
                                          AND field_key = ?
                                        """
            c.execute(sql_update_fieldposition, (dataset_id, str(field_key), position,))
            self.__conn.commit()
            c.close()
        except sqlite3.Error as e:
            logger.exception("sql failed with error")
        logger.info("Finished")

    def DeleteField(self, dataset_key, field_key):
        logger = logging.getLogger(__name__+".DeleteField")
        logger.info("Starting")
        try:
            c = self.__conn.cursor()
            sql_select_datasetid = """SELECT id
                                      FROM datasets 
                                      WHERE dataset_key = ?
                                      """
            c.execute(sql_select_datasetid, (str(dataset_key),))
            dataset_id = c.fetchone()[0]
            sql_delete_field = """DELETE FROM fields
                                  WHERE dataset_id = ?
                                  AND field_key = ?
                                  """
            c.execute(sql_delete_field, (dataset_id, str(field_key),))
            self.__conn.commit()
            c.close()
        except sqlite3.Error as e:
            logger.exception("sql failed with error")
        logger.info("Finished")

    def CheckIfFieldExists(self, dataset_key, field_key):
        logger = logging.getLogger(__name__+".CheckIfFieldInStringTokens")
        logger.info("Starting")
        value = False
        try:
            c = self.__conn.cursor()
            sql_select_datasetid = """SELECT id
                                      FROM datasets 
                                      WHERE dataset_key = ?
                                      """
            c.execute(sql_select_datasetid, (str(dataset_key),))
            dataset_id = c.fetchone()[0]
            sql_fieldexists_query = """SELECT 1
                                       FROM fields
                                       WHERE dataset_id = ?
                                       and field_key = ?
                                        """
            c.execute(sql_fieldexists_query, (dataset_id, str(field_key),))
            if c.fetchone() != None:
                value= True
            c.close()
        except sqlite3.Error as e:
            logger.exception("sql failed with error")
        logger.info("Finished")
        return value
    
    def InsertDocuments(self, dataset_key, document_keys):
        logger = logging.getLogger(__name__+".InsertDataset")
        logger.info("Starting")
        old_isolation_level = self.__conn.isolation_level
        self.__conn.isolation_level = None
        try:
            c = self.__conn.cursor()
            c.execute("BEGIN")
            sql_select_datasetid = """SELECT id
                                      FROM datasets 
                                      WHERE dataset_key = ?
                                      """
            c.execute(sql_select_datasetid, (str(dataset_key),))
            dataset_id = c.fetchone()[0]
            for document_key in document_keys:
                sql_insert_tokens = """INSERT INTO documents (
                                            dataset_id,
                                            document_key
                                            ) values (?, ?)"""
                c.execute(sql_insert_tokens, (dataset_id, str(document_key),))
            c.execute("COMMIT")
            c.close()
        except sqlite3.Error as e:
            logger.exception("sql failed with error")
        finally:
            self.__conn.isolation_level = old_isolation_level
        logger.info("Finished")

    #Function used during processing
    def InsertStringTokens(self, dataset_key, field_key, tokens):
        logger = logging.getLogger(__name__+".InsertStringTokens")
        logger.info("Starting")
        old_isolation_level = self.__conn.isolation_level
        self.__conn.isolation_level = None
        try:
            c = self.__conn.cursor()
            sql_select_datasetid = """SELECT id
                                      FROM datasets 
                                      WHERE dataset_key = ?
                                      """
            c.execute(sql_select_datasetid, (str(dataset_key),))
            dataset_id = c.fetchone()[0]
            sql_select_fieldid = """SELECT id
                                    FROM fields
                                    WHERE dataset_id = ?
                                    AND field_key = ?
                                    """
            c.execute(sql_select_fieldid, (dataset_id, str(field_key),))
            field_id = c.fetchone()[0]
            sql_insert_tokens = """INSERT INTO string_tokens (
                                        dataset_id,
                                        field_id,
                                        document_id,
                                        position,
                                        text,
                                        stem,
                                        lemma,
                                        pos,
                                        spacy_stopword
                                        ) values (?,?,?,?,?,?,?,?,?)"""
            c.execute("BEGIN")
            for doc_key in tokens:
                sql_select_documentid = """SELECT id
                                        FROM documents 
                                        WHERE dataset_id = ?
                                        AND document_key = ?
                                        """
                c.execute(sql_select_documentid, (dataset_id, str(doc_key),))
                document_id = c.fetchone()[0]
                for t in tokens[doc_key]:
                    c.execute(sql_insert_tokens, (dataset_id, field_id, document_id, t[0], t[1], t[2], t[3], t[4], t[5],))
            c.execute("COMMIT")
            c.close()
        except sqlite3.Error as e:
            logger.exception("sql failed with error")
        finally:
            self.__conn.isolation_level = old_isolation_level
        logger.info("Finished")
    
    def UpdateStringTokensTFIDF(self, dataset_key):
        logger = logging.getLogger(__name__+".UpdateStringTokensTFIDF")
        logger.info("Starting")
        try:
            c = self.__conn.cursor()
            sql_select_datasetid = """SELECT id
                                      FROM datasets 
                                      WHERE dataset_key = ?
                                      """
            c.execute(sql_select_datasetid, (str(dataset_key),))
            dataset_id = c.fetchone()[0]
            # for each token row:
            # 1) calculate tf
            sql_update_stemtf = """UPDATE string_tokens
                                   SET text_tf = token_counts.cnt
                                   FROM (SELECT dataset_id, text, dataset_id, COUNT(*) as cnt
                                         FROM string_tokens
                                         WHERE dataset_id = ?
                                         GROUP BY dataset_id, text, dataset_id) AS token_counts
                                   WHERE string_tokens.dataset_id = token_counts.dataset_id
                                   AND string_tokens.text = token_counts.text
                                   AND string_tokens.dataset_id = token_counts.dataset_id
                                   """
            c.execute(sql_update_stemtf, (dataset_id,))
            sql_update_stemtf = """UPDATE string_tokens
                                   SET stem_tf = token_counts.cnt
                                   FROM (SELECT dataset_id, stem, dataset_id, COUNT(*) as cnt
                                         FROM string_tokens
                                         WHERE dataset_id = ?
                                         GROUP BY dataset_id, stem, dataset_id) AS token_counts
                                   WHERE string_tokens.dataset_id = token_counts.dataset_id
                                   AND string_tokens.stem = token_counts.stem
                                   AND string_tokens.dataset_id = token_counts.dataset_id
                                   """
            c.execute(sql_update_stemtf, (dataset_id,))
            sql_update_lemmatf = """UPDATE string_tokens
                                    SET lemma_tf = token_counts.cnt
                                    FROM (SELECT dataset_id, lemma, dataset_id, COUNT(*) as cnt
                                          FROM string_tokens
                                          WHERE dataset_id = ?
                                          GROUP BY dataset_id, lemma, dataset_id) AS token_counts
                                    WHERE string_tokens.dataset_id = token_counts.dataset_id
                                    AND string_tokens.lemma = token_counts.lemma
                                    AND string_tokens.dataset_id = token_counts.dataset_id
                                    """
            c.execute(sql_update_lemmatf, (dataset_id,))
            self.__conn.commit()

            # 2b) calculate idf using log(doc count / document_frequency)
            sql_select_documentscount = """SELECT COUNT(DISTINCT document_key)
                                           FROM documents
                                           WHERE dataset_id = ?"""
            c.execute(sql_select_documentscount, (dataset_id,))
            document_count = c.fetchone()[0]

            sql_select_documentcountpertext = """SELECT text, COUNT(DISTINCT document_id)
                                                 FROM string_tokens
                                                 WHERE dataset_id = ?
                                                 GROUP BY text"""
            c.execute(sql_select_documentcountpertext, (dataset_id,))
            text_idf_list = []
            for text, count in c.fetchall():
                text_idf_list.append((log(document_count/count), dataset_id, text,))
            sql_update_textidf = """UPDATE string_tokens
                                    SET text_idf = ?
                                    WHERE dataset_id = ?
                                    AND text = ?
                                    """
            c.executemany(sql_update_textidf, text_idf_list)

            sql_select_documentcountperstem = """SELECT stem, COUNT(DISTINCT document_id)
                                                 FROM string_tokens
                                                 WHERE dataset_id = ?
                                                 GROUP BY stem"""
            c.execute(sql_select_documentcountperstem, (dataset_id,))
            stem_idf_list = []
            for stem, count in c.fetchall():
                stem_idf_list.append((log(document_count/count), dataset_id, stem,))
            sql_update_stemidf = """UPDATE string_tokens
                                    SET stem_idf = ?
                                    WHERE dataset_id = ?
                                    AND stem = ?
                                    """
            c.executemany(sql_update_stemidf, stem_idf_list)

            sql_select_documentcountperlemma = """SELECT lemma, COUNT(DISTINCT document_id)
                                                  FROM string_tokens
                                                  WHERE dataset_id = ?
                                                  GROUP BY stem"""
            c.execute(sql_select_documentcountperlemma, (dataset_id,))
            lemma_idf_list = []
            for lemma, count in c.fetchall():
                lemma_idf_list.append((log(document_count/count), dataset_id, lemma,))
            sql_update_lemmaidf = """UPDATE string_tokens
                                     SET lemma_idf = ?
                                     WHERE dataset_id = ?
                                     AND lemma = ?
                                     """
            c.executemany(sql_update_lemmaidf, lemma_idf_list)
            self.__conn.commit()
            
            # 3) calculate tf-idf and multiplying tf by idf
            sql_update_tfidf = """UPDATE string_tokens
                                  SET text_tfidf = text_tf * text_idf,
                                      stem_tfidf = stem_tf * stem_idf,
                                      lemma_tfidf = lemma_tf * lemma_idf
                                  WHERE dataset_id = ?
                                  """
            c.execute(sql_update_tfidf, (dataset_id,))
            self.__conn.commit()

            c.close()
        except sqlite3.Error as e:
            logger.exception("sql failed with error")
        logger.info("Finished")

    def ApplyDatasetRules(self, dataset_key, rules):
        logger = logging.getLogger(__name__+".ApplyRulesToStringTokens")
        logger.info("Starting")
        try:
            c = self.__conn.cursor()
            sql_select_dataset = """SELECT id, token_type
                                      FROM datasets 
                                      WHERE dataset_key = ?
                                      """
            c.execute(sql_select_dataset, (str(dataset_key),))
            result = c.fetchone()
            dataset_id = result[0]
            token_type = result[1]

            
            query_totalwordcount_sql = """SELECT COUNT(*)
                                          FROM string_tokens
                                          WHERE dataset_id = ?
                                          """
            
            query_totaldoccount_sql = """SELECT COUNT(DISTINCT document_id)
                                         FROM string_tokens
                                         WHERE dataset_id = ?
                                         """

            update_sql = """UPDATE string_tokens
                              SET included = ?
                              WHERE dataset_id = ?
                              """

            #special code needed to figure out tfidf positions
            update_tfidflower_sql = """UPDATE string_tokens
                                       SET included = ?
                                       FROM (SELECT id, 
                                                    PERCENT_RANK() OVER(ORDER BY CASE ?
                                                                                 WHEN 'stem' THEN stem_tfidf
                                                                                 WHEN 'lemma' THEN lemma_tfidf
                                                                                 ELSE text_tfidf
                                                                                 END ASC
                                                                       ) as per_rank
                                             FROM string_tokens
                                             WHERE dataset_id = ?
                                            ) as ranktable
                                       WHERE ranktable.id = string_tokens.id
                                       AND per_rank < ?
                                       """
            
            update_tfidfupper_sql = """UPDATE string_tokens
                                       SET included = ?
                                       FROM (SELECT id, 
                                                    PERCENT_RANK() OVER(ORDER BY CASE ?
                                                                                 WHEN 'stem' THEN stem_tfidf
                                                                                 WHEN 'lemma' THEN lemma_tfidf
                                                                                 ELSE text_tfidf
                                                                                 END DESC
                                                                       ) as per_rank
                                             FROM string_tokens
                                             WHERE dataset_id = ?
                                            ) as ranktable
                                       WHERE ranktable.id = string_tokens.id
                                       AND per_rank < ?
                                       """

            #special code needed for number filters
            
            update_count_sql1 = """UPDATE string_tokens
                                   SET included = ?
                                   FROM (
                                   """
            subquery_count_sql2 = """GROUP BY CASE ?
                                              WHEN 'stem' THEN stem
                                              WHEN 'lemma' THEN lemma
                                              ELSE text
                                              END,
                                              pos
                                     """
            subquery_wordcount_sql1 = """SELECT CASE ?
                                                WHEN 'stem' THEN stem
                                                WHEN 'lemma' THEN lemma
                                                ELSE text
                                                END word,
                                                pos,
                                                COUNT(*) as count
                                         FROM string_tokens
                                         WHERE dataset_id = ?
                                         """
            subquery_doccount_sql1 = """SELECT CASE ?
                                               WHEN 'stem' THEN stem
                                               WHEN 'lemma' THEN lemma
                                               ELSE text
                                               END word,
                                               pos,
                                               COUNT(DISTINCT document_id) as count
                                        FROM string_tokens
                                        WHERE dataset_id = ?
                                        """
            update_count_sql2 = """) as counttable
                                       WHERE dataset_id = ?
                                       AND counttable.word = CASE ?
                                                             WHEN 'stem' THEN stem
                                                             WHEN 'lemma' THEN lemma
                                                             ELSE text
                                                             END
                                       AND counttable.pos = string_tokens.pos
                                       AND counttable.count"""

            #number filter symbol
            gt_sql = """ > ?
                        """
            gteq_sql = """ >= ?
                        """
            eq_sql = """ = ?
                        """
            lteq_sql = """ <= ?
                        """
            lt_sql = """ < ?
                        """
            
            #stopword filter
            stopwords_sql = """AND spacy_stopword = 1
                               """

            #string filters
            word_sql = """AND CASE ?
                            WHEN 'stem' THEN stem
                            WHEN 'lemma' THEN lemma
                            ELSE text
                            END = ?
                            """
            pos_sql = """AND pos = ?
                         """
            field_sql = """AND field_id = (SELECT id
                                           FROM fields
                                           WHERE fields.dataset_id = dataset_id
                                           AND field_key = ?)
                           """

            #reset included to default for all strings
            c.execute(update_sql, (1, dataset_id,))
            self.__conn.commit()

            #apply rules in order
            for field, word, pos, action in rules:
                sql_filters = ""
                sql_filters_parameters = []
                if word != Constants.FILTER_RULE_ANY:
                    sql_filters = sql_filters + word_sql
                    sql_filters_parameters.append(token_type)
                    sql_filters_parameters.append(word)
                if pos != Constants.FILTER_RULE_ANY:
                    sql_filters = sql_filters + pos_sql
                    sql_filters_parameters.append(pos)
                if field != Constants.FILTER_RULE_ANY:
                    sql_filters = sql_filters + field_sql
                    sql_filters_parameters.append(str(field))

                sql = ""
                sql_parameters = []
                if action == Constants.FILTER_RULE_REMOVE:
                    sql = update_sql
                    sql_parameters.append(0)
                    sql_parameters.append(dataset_id)
                elif action == Constants.FILTER_RULE_INCLUDE:
                    sql = update_sql
                    sql_parameters.append(1)
                    sql_parameters.append(dataset_id)
                elif action == Constants.FILTER_RULE_REMOVE_SPACY_AUTO_STOPWORDS:
                    sql = update_sql + stopwords_sql
                    sql_parameters.append(0)
                    sql_parameters.append(dataset_id)
                elif isinstance(action, tuple):
                    if action[0] == Constants.FILTER_TFIDF_REMOVE:
                        sql_parameters.append(0)
                        sql_parameters.append(token_type)
                        sql_parameters.append(dataset_id)
                        sql_parameters.append(action[2]/100)
                        if action[1] == Constants.FILTER_TFIDF_LOWER:
                            sql = update_tfidflower_sql
                        elif action[1] == Constants.FILTER_TFIDF_UPPER:
                            sql = update_tfidfupper_sql
                    elif action[0] == Constants.FILTER_TFIDF_INCLUDE:
                        sql_parameters.append(1)
                        sql_parameters.append(token_type)
                        sql_parameters.append(dataset_id)
                        sql_parameters.append(action[2]/100)
                        if action[1] == Constants.FILTER_TFIDF_LOWER:
                            sql = update_tfidflower_sql
                        elif action[1] == Constants.FILTER_TFIDF_UPPER:
                            sql = update_tfidfupper_sql
                    elif action[0] == Constants.FILTER_RULE_REMOVE or action[0] == Constants.FILTER_RULE_INCLUDE:
                        if action[0] == Constants.FILTER_RULE_REMOVE:
                            sql_parameters.append(0)
                        else:
                            sql_parameters.append(1)
                        sql_parameters.append(token_type)
                        sql_parameters.append(dataset_id)
                        sql_parameters = sql_parameters + sql_filters_parameters
                        sql_parameters.append(token_type)
                        sql_parameters.append(dataset_id)
                        sql_parameters.append(token_type)

                        if action[1] == Constants.TOKEN_NUM_WORDS:
                            sql = update_count_sql1+subquery_wordcount_sql1+sql_filters+subquery_count_sql2+update_count_sql2
                            sql_parameters.append(action[3])
                        elif action[1] == Constants.TOKEN_PER_WORDS:
                            sql = update_count_sql1+subquery_wordcount_sql1+sql_filters+subquery_count_sql2+update_count_sql2
                            c.execute(query_totalwordcount_sql, (dataset_id,))
                            total_words = c.fetchone()[0]
                            sql_parameters.append(action[3]/100*total_words)
                        elif action[1] == Constants.TOKEN_NUM_DOCS:
                            sql = update_count_sql1+subquery_doccount_sql1+sql_filters+subquery_count_sql2+update_count_sql2
                            sql_parameters.append(action[3])
                        elif action[1] == Constants.TOKEN_PER_DOCS:
                            sql = update_count_sql1+subquery_doccount_sql1+sql_filters+subquery_count_sql2+update_count_sql2
                            c.execute(query_totaldoccount_sql, (dataset_id,))
                            total_docs = c.fetchone()[0]
                            sql_parameters.append(action[3]/100*total_docs)

                        if action[2] == ">":
                            sql = sql + gt_sql
                        elif action[2] == ">=":
                            sql = sql + gteq_sql
                        elif action[2] == "=":
                            sql = sql + eq_sql
                        elif action[2] == "<=":
                            sql = sql + lteq_sql
                        elif action[2] == "<":
                            sql = sql + lt_sql

                #execute the rule
                sql = sql+sql_filters
                sql_parameters = sql_parameters + sql_filters_parameters
                c.execute(sql, sql_parameters)

                #commit after every rule to make sure operations are applied in order
                self.__conn.commit()

            c.close()
        except sqlite3.Error as e:
            logger.exception("sql failed with error")
        logger.info("Finished")

    def GetStringTokensCounts(self, dataset_key):
        logger = logging.getLogger(__name__+".GetStringTokensCounts")
        logger.info("Starting")
        counts={}
        try:
            c = self.__conn.cursor()
            sql_select_datasetid = """SELECT id
                                      FROM datasets 
                                      WHERE dataset_key = ?
                                      """
            c.execute(sql_select_datasetid, (str(dataset_key),))
            dataset_id = c.fetchone()[0]

            sql_tokencount_query = """SELECT COUNT(*)
                                      FROM string_tokens
                                      WHERE dataset_id = ?
                                      """
            c.execute(sql_tokencount_query, (dataset_id,))
            cur_result = c.fetchone()
            counts['tokens'] = cur_result[0]

            sql_uniquetokencount_query = """SELECT CASE (SELECT datasets.token_type FROM datasets WHERE datasets.id = dataset_id)
                                                        WHEN 'stem' THEN COUNT(DISTINCT stem)
                                                        WHEN 'lemma' THEN COUNT(DISTINCT lemma)
                                                        ELSE COUNT(DISTINCT text)
                                                        END         
                                            FROM string_tokens
                                            WHERE dataset_id = ?
                                            """
            c.execute(sql_uniquetokencount_query, (dataset_id,))
            cur_result = c.fetchone()
            counts['unique_tokens'] = cur_result[0]

            sql_documentcount_query = """SELECT COUNT(DISTINCT document_id)
                                         FROM string_tokens
                                         WHERE dataset_id = ?
                                         """
            c.execute(sql_documentcount_query, (dataset_id,))
            cur_result = c.fetchone()
            counts['documents'] = cur_result[0]

            c.close()
        except sqlite3.Error as e:
            logger.exception("sql failed with error")
        logger.info("Finished")
        return counts

    def GetIncludedStringTokensCounts(self, dataset_key):
        logger = logging.getLogger(__name__+".GetIncludedStringTokensCounts")
        logger.info("Starting")
        counts={}
        try:
            c = self.__conn.cursor()
            sql_select_datasetid = """SELECT id
                                      FROM datasets 
                                      WHERE dataset_key = ?
                                      """
            c.execute(sql_select_datasetid, (str(dataset_key),))
            dataset_id = c.fetchone()[0]

            sql_tokencount_query = """SELECT COUNT(*)
                                      FROM string_tokens
                                      WHERE dataset_id = ?
                                      AND included = 1
                                      """
            c.execute(sql_tokencount_query, (str(dataset_id),))
            cur_result = c.fetchone()
            counts['tokens'] = cur_result[0]

            sql_uniquetokencount_query = """SELECT CASE (SELECT datasets.token_type FROM datasets WHERE datasets.id = dataset_id)
                                                        WHEN 'stem' THEN COUNT(DISTINCT stem)
                                                        WHEN 'lemma' THEN COUNT(DISTINCT lemma)
                                                        ELSE COUNT(DISTINCT text)
                                                        END         
                                            FROM string_tokens
                                            WHERE dataset_id = ?
                                            AND included = 1
                                            """
            c.execute(sql_uniquetokencount_query, (dataset_id,))
            cur_result = c.fetchone()
            counts['unique_tokens'] = cur_result[0]

            sql_documentcount_query = """SELECT COUNT(DISTINCT document_id)
                                         FROM string_tokens
                                         WHERE dataset_id = ?
                                         AND included = 1
                                         """
            c.execute(sql_documentcount_query, (dataset_id,))
            cur_result = c.fetchone()
            counts['documents'] = cur_result[0]

            c.close()
        except sqlite3.Error as e:
            logger.exception("sql failed with error")
        logger.info("Finished")
        return counts

    def GetIncludedStringTokensDataFrame(self, dataset_key):
        logger = logging.getLogger(__name__+".GetIncludedStringTokensDataFrame")
        logger.info("Starting")
        try:
            c = self.__conn.cursor()
            sql_select_datasetid = """SELECT id
                                      FROM datasets 
                                      WHERE dataset_key = ?
                                      """
            c.execute(sql_select_datasetid, (str(dataset_key),))
            dataset_id = c.fetchone()[0]
            c.close()
            df = pd.read_sql("""SELECT 
                                words,
                                pos,
                                num_of_words,
                                num_of_docs,
                                spacy_stopword,
                                tfidf_range
                                FROM string_tokens_included_view WHERE dataset_id = ?""", self.__conn, params=(dataset_id,))
            df['spacy_stopword'] = df['spacy_stopword'].astype(bool)
        except sqlite3.Error as e:
            logger.exception("sql failed with error")
        logger.info("Finished")
        return df

    def GetRemovedStringTokensDataFrame(self, dataset_key):
        logger = logging.getLogger(__name__+".GetRemovedStringTokensDataFrame")
        logger.info("Starting")
        try:
            c = self.__conn.cursor()
            sql_select_datasetid = """SELECT id
                                      FROM datasets 
                                      WHERE dataset_key = ?
                                      """
            c.execute(sql_select_datasetid, (str(dataset_key),))
            dataset_id = c.fetchone()[0]
            c.close()
            df = pd.read_sql("""SELECT 
                                words,
                                pos,
                                num_of_words,
                                num_of_docs,
                                spacy_stopword,
                                tfidf_range
                                FROM string_tokens_removed_view WHERE dataset_id = ?""", self.__conn, params=(dataset_id,))
            df['spacy_stopword'] = df['spacy_stopword'].astype(bool)
        except sqlite3.Error as e:
            logger.exception("sql failed with error")
        logger.info("Finished")
        return df

    def GetDocumentsTokensFromStringTokens(self, dataset_key):
        logger = logging.getLogger(__name__+".GetDocumentsTokensFromStringTokens")
        logger.info("Starting")
        tokens_dict = {}
        try:
            c = self.__conn.cursor()
            sql_select_documenttokens = """SELECT document_key,
                                                 GROUP_CONCAT(word, " ") 
                                           FROM (SELECT document_key,
                                                        CASE (SELECT datasets.token_type 
                                                              FROM datasets
                                                              WHERE datasets.id = string_tokens.dataset_id)
                                                        WHEN 'stem' THEN stem
                                                        WHEN 'lemma' THEN lemma
                                                        ELSE text
                                                        END as word
                                                 FROM string_tokens
                                                 LEFT JOIN  documents ON
                                                    string_tokens.document_id = documents.id
                                                 WHERE included = 1
                                                 AND string_tokens.dataset_id = (SELECT id
                                                                                 FROM datasets 
                                                                                 WHERE dataset_key = ?)
                                                 ORDER BY string_tokens.document_id ASC,
                                                          string_tokens.field_id ASC,
                                                          string_tokens.position ASC)
                                           GROUP BY document_key
                                           """
            tokens_dict = {}
            c.execute(sql_select_documenttokens, (str(dataset_key),))
            for row in c.fetchall():
                tokens_dict[eval(row[0])] = row[1].split()
            c.close()
        except sqlite3.Error as e:
            logger.exception("sql failed with error")
        logger.info("Finished")
        return tokens_dict

