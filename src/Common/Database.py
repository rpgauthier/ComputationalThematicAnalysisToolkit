import logging
import sqlite3
import math
import os.path

import Common.Constants as Constants
from Common.GUIText import Filtering as GUITextFiltering

class DatabaseConnection():
    def __init__(self, current_workspace_path):
        database_path = os.path.join(current_workspace_path, "workspace_sqlite3.db")
        self.__conn = sqlite3.connect(database_path)
        self.__conn.execute("PRAGMA foreign_keys=ON")
    
    def __del__(self):

        self.__conn.close()

    def Create(self):
        logger = logging.getLogger(__name__+".Create")
        logger.info("Starting")
        try:
            c = self.__conn.cursor()

            sql_createtable_datasets = """ CREATE TABLE IF NOT EXISTS datasets (
                                                    id INTEGER PRIMARY KEY,
                                                    dataset_key TEXT UNIQUE,
                                                    token_type TEXT
                                                )"""
            c.execute(sql_createtable_datasets)

            sql_createtable_datasets = """ CREATE TABLE IF NOT EXISTS fields (
                                                    id INTEGER PRIMARY KEY,
                                                    dataset_id, INTEGER,
                                                    field_key TEXT,
                                                    position INT,
                                                    FOREIGN KEY(dataset_id) REFERENCES datasets(id)
                                                        ON UPDATE CASCADE
                                                        ON DELETE CASCADE,
                                                    UNIQUE(dataset_id, field_key)
                                                )"""
            c.execute(sql_createtable_datasets)

            sql_createtable_datasets = """ CREATE TABLE IF NOT EXISTS documents (
                                                    id INTEGER PRIMARY KEY,
                                                    dataset_id, INTEGER,
                                                    document_key TEXT,
                                                    FOREIGN KEY(dataset_id) REFERENCES datasets(id)
                                                        ON UPDATE CASCADE
                                                        ON DELETE CASCADE,
                                                    UNIQUE(dataset_id, document_key)
                                                )"""
            c.execute(sql_createtable_datasets)

            sql_createtable_stringtokens = """ CREATE TABLE IF NOT EXISTS string_tokens (
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
            c.execute(sql_createtable_stringtokens)

            sql_create_text_index = """CREATE INDEX IF NOT EXISTS string_tokens_text_index ON string_tokens(dataset_id, text, document_id)"""
            c.execute(sql_create_text_index)

            sql_create_stem_index = """CREATE INDEX IF NOT EXISTS string_tokens_stem_index ON string_tokens(dataset_id, stem, document_id)"""
            c.execute(sql_create_stem_index)

            sql_create_lemma_index = """CREATE INDEX IF NOT EXISTS string_tokens_lemma_index ON string_tokens(dataset_id, lemma, document_id)"""
            c.execute(sql_create_lemma_index)

            sql_create_included_index = """CREATE INDEX IF NOT EXISTS string_tokens_included_index ON string_tokens(dataset_id, included)"""
            c.execute(sql_create_included_index)

            sql_create_text_index = """CREATE INDEX IF NOT EXISTS string_tokens_field_id_index ON string_tokens(field_id)"""
            c.execute(sql_create_text_index)

            sql_create_text_index = """CREATE INDEX IF NOT EXISTS string_tokens_document_id_index ON string_tokens(document_id)"""
            c.execute(sql_create_text_index)

            sql_createtable_stringtokensincluded = """CREATE TABLE IF NOT EXISTS string_tokens_included (
                                                            id INTEGER PRIMARY KEY,
                                                            dataset_id INTEGER,
                                                            words TEXT,
                                                            pos TEXT,
                                                            num_of_words, INTEGER,
                                                            num_of_docs INTEGER,
                                                            spacy_stopword BOOLEAN,
                                                            tfidf_range_min FLOAT,
                                                            tfidf_range_max FLOAT,
                                                            FOREIGN KEY(dataset_id) REFERENCES datasets(id)
                                                                ON UPDATE CASCADE
                                                                ON DELETE CASCADE
                                                        )"""
            c.execute(sql_createtable_stringtokensincluded)

            sql_createtable_stringtokensremoved = """CREATE TABLE IF NOT EXISTS string_tokens_removed (
                                                            id INTEGER PRIMARY KEY,
                                                            dataset_id INTEGER,
                                                            words TEXT,
                                                            pos TEXT,
                                                            num_of_words, INTEGER,
                                                            num_of_docs INTEGER,
                                                            spacy_stopword BOOLEAN,
                                                            tfidf_range_min FLOAT,
                                                            tfidf_range_max FLOAT,
                                                            FOREIGN KEY(dataset_id) REFERENCES datasets(id)
                                                                ON UPDATE CASCADE
                                                                ON DELETE CASCADE
                                                       )"""
            c.execute(sql_createtable_stringtokensremoved)

            self.__conn.commit()
            c.close()
        except sqlite3.Error:
            logger.exception("sql failed with sql error")
        logger.info("Finished")

    #TODO figure out how to drop columns tf and idf if they exist as they are no longer used
    def Upgrade(self):
        logger = logging.getLogger(__name__+".Upgrade")
        logger.info("Starting")
        try:
            c = self.__conn.cursor()

            self.Create()
            c.execute("""DROP VIEW IF EXISTS string_tokens_included_view""")
            c.execute("""DROP VIEW IF EXISTS string_tokens_removed_view""")
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
            sql_update_fieldposition = """UPDATE fields
                                          SET position = ?
                                          WHERE dataset_id = (SELECT id
                                                              FROM datasets 
                                                              WHERE dataset_key = ?)
                                          AND field_key = ?
                                        """
            c.execute(sql_update_fieldposition, (position, str(dataset_key), str(field_key),))
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
            sql_delete_field = """DELETE FROM fields
                                  WHERE dataset_id = (SELECT id
                                                      FROM datasets 
                                                      WHERE dataset_key = ?)
                                  AND field_key = ?
                                  """
            c.execute(sql_delete_field, (str(dataset_key), str(field_key),))
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
            sql_fieldexists_query = """SELECT 1
                                       FROM fields
                                       WHERE dataset_id = (SELECT id
                                                           FROM datasets 
                                                           WHERE dataset_key = ?)
                                       and field_key = ?
                                        """
            c.execute(sql_fieldexists_query, (str(dataset_key), str(field_key),))
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
            parameters = []
            for document_key in document_keys:
                parameters.append((dataset_id, str(document_key),))
            sql_insert_tokens = """INSERT INTO documents (
                                          dataset_id,
                                          document_key
                                          ) values (?, ?)"""
            c.executemany(sql_insert_tokens, parameters)
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

            sql_select_documentid = """SELECT id
                                       FROM documents 
                                       WHERE dataset_id = ?
                                       AND document_key = ?
                                       """
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
                c.execute(sql_select_documentid, (dataset_id, str(doc_key),))
                document_id = c.fetchone()[0]
                parameters = []
                for t in tokens[doc_key]:
                    parameters.append((dataset_id, field_id, document_id, t[0], t[1], t[2], t[3], t[4], t[5],))
                c.executemany(sql_insert_tokens, parameters)
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

            self.__conn.create_function('log', 1, math.log)

            sql_select_datasetid = """SELECT id
                                      FROM datasets 
                                      WHERE dataset_key = ?
                                      """
            c.execute(sql_select_datasetid, (str(dataset_key),))
            dataset_id = c.fetchone()[0]

            sql_select_documentscount = """SELECT COUNT(DISTINCT document_key)
                                           FROM documents
                                           WHERE dataset_id = ?"""
            c.execute(sql_select_documentscount, (dataset_id,))
            document_count = c.fetchone()[0]

            #1) For Text
            sql_texttf = """SELECT dataset_id,
                                   text,
                                   document_id,
                                   COUNT(*) as tf
                            FROM string_tokens
                            WHERE dataset_id = :dataset_id
                            GROUP BY dataset_id, text, document_id
                            """

            sql_textidf = """SELECT dataset_id,
                                    text,
                                    log(CAST(:document_count as REAL)/COUNT(DISTINCT document_id)) as idf
                             FROM string_tokens
                             WHERE dataset_id = :dataset_id
                             GROUP BY dataset_id, text
                             """

            sql_update_texttfidf = """UPDATE string_tokens
                                      SET text_tfidf = tmp_tfidf.tfidf
                                      FROM (SELECT text_tf.dataset_id AS dataset_id,
                                                   text_tf.text AS text ,
                                                   text_tf.document_id AS document_id,
                                                   text_tf.tf * text_idf.idf AS tfidf
                                            FROM ("""+sql_texttf+""") AS text_tf
                                            JOIN ("""+sql_textidf+""") AS text_idf
                                            ON text_tf.text = text_idf.text
                                            ) AS tmp_tfidf
                                      WHERE string_tokens.dataset_id = tmp_tfidf.dataset_id
                                      AND string_tokens.text = tmp_tfidf.text
                                      AND string_tokens.document_id = tmp_tfidf.document_id
                                      """
            c.execute(sql_update_texttfidf, {'dataset_id':dataset_id, 'document_count': document_count})
            logger.info("Updated Text tf-idf")

            #2) for Stem
            sql_stemtf = """SELECT dataset_id,
                                   stem,
                                   document_id,
                                   COUNT(*) as tf
                            FROM string_tokens
                            WHERE dataset_id = :dataset_id
                            GROUP BY dataset_id, stem, document_id
                            """

            sql_stemidf = """SELECT dataset_id,
                                    stem,
                                    log(CAST(:document_count as REAL)/COUNT(DISTINCT document_id)) as idf
                             FROM string_tokens
                             WHERE dataset_id = :dataset_id
                             GROUP BY dataset_id, stem
                             """

            sql_update_stemtfidf = """UPDATE string_tokens
                                      SET stem_tfidf = tmp_tfidf.tfidf
                                      FROM (SELECT stem_tf.dataset_id AS dataset_id,
                                                   stem_tf.stem AS stem ,
                                                   stem_tf.document_id AS document_id,
                                                   stem_tf.tf * stem_idf.idf AS tfidf
                                            FROM ("""+sql_stemtf+""") AS stem_tf
                                            JOIN ("""+sql_stemidf+""") AS stem_idf
                                            ON stem_tf.stem = stem_idf.stem
                                            ) AS tmp_tfidf
                                      WHERE string_tokens.dataset_id = tmp_tfidf.dataset_id
                                      AND string_tokens.stem = tmp_tfidf.stem
                                      AND string_tokens.document_id = tmp_tfidf.document_id
                                      """
            c.execute(sql_update_stemtfidf, {'dataset_id':dataset_id, 'document_count': document_count})
            logger.info("Updated Stem tf-idf")

            #3) For Lemma
            sql_lemmatf = """SELECT dataset_id,
                                    lemma,
                                    document_id,
                                    COUNT(*) as tf
                             FROM string_tokens
                             WHERE dataset_id = :dataset_id
                             GROUP BY dataset_id, lemma, document_id
                            """
            
            sql_lemmaidf = """SELECT dataset_id,
                                     lemma,
                                     log(CAST(:document_count as REAL)/COUNT(DISTINCT document_id)) as idf
                              FROM string_tokens
                              WHERE dataset_id = :dataset_id
                              GROUP BY dataset_id, lemma
                              """

            sql_update_lemmatfidf = """UPDATE string_tokens
                                       SET lemma_tfidf = tmp_tfidf.tfidf
                                       FROM (SELECT lemma_tf.dataset_id AS dataset_id,
                                                    lemma_tf.lemma AS lemma ,
                                                    lemma_tf.document_id AS document_id,
                                                    lemma_tf.tf * lemma_idf.idf AS tfidf
                                             FROM ("""+sql_lemmatf+""") AS lemma_tf
                                             JOIN ("""+sql_lemmaidf+""") AS lemma_idf
                                             ON lemma_tf.lemma = lemma_idf.lemma
                                             ) AS tmp_tfidf
                                       WHERE string_tokens.dataset_id = tmp_tfidf.dataset_id
                                       AND string_tokens.lemma = tmp_tfidf.lemma
                                       AND string_tokens.document_id = tmp_tfidf.document_id
                                       """
            c.execute(sql_update_lemmatfidf, {'dataset_id':dataset_id, 'document_count': document_count})
            logger.info("Updated Lemma tf-idf")

            self.__conn.commit()
            c.close()
        except sqlite3.Error as e:
            logger.exception("sql failed with error")
        logger.info("Finished")

    #TODO check if additional indexes are needed to further optimize rule application
    def ApplyDatasetRules(self, dataset_key, rules):
        logger = logging.getLogger(__name__+".ApplyDatasetRules")
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
            
            query_totalwordcount_sql = """SELECT COUNT(*),
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
                                                    ) AS per_rank
                                             FROM string_tokens
                                             WHERE dataset_id = ?
                                            ) AS ranktable
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
                                                    ) AS per_rank
                                             FROM string_tokens
                                             WHERE dataset_id = ?
                                            ) AS ranktable
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
                                                COUNT(*) AS count
                                         FROM string_tokens
                                         WHERE dataset_id = ?
                                         """
            subquery_doccount_sql1 = """SELECT CASE ?
                                               WHEN 'stem' THEN stem
                                               WHEN 'lemma' THEN lemma
                                               ELSE text
                                               END word,
                                               pos,
                                               COUNT(DISTINCT document_id) AS count
                                        FROM string_tokens
                                        WHERE dataset_id = ?
                                        """
            update_count_sql2 = """) AS counttable
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

                #commit after every rule to make sure operations are applied in correct order
                self.__conn.commit()
            
                logger.info("Completed Applying Rule (%s, %s, %s, %s)", str(field), str(word), str(pos), str(action))
            c.close()
        except sqlite3.Error as e:
            logger.exception("sql failed with error")
        logger.info("Finished")
    
    #TODO check if additional indexes are needed to optimize rule application performance
    def ApplyDatasetRule(self, dataset_key, rule):
        logger = logging.getLogger(__name__+".ApplyDatasetRule")
        logger.info("Starting Applying Rule %s", str(rule))
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
                                                                ) AS per_rank
                                             FROM string_tokens
                                             WHERE dataset_id = ?
                                            ) AS ranktable
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
                                                                ) AS per_rank
                                             FROM string_tokens
                                             WHERE dataset_id = ?
                                            ) AS ranktable
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
                                                COUNT(*) AS count
                                         FROM string_tokens
                                         WHERE dataset_id = ?
                                         """
            subquery_doccount_sql1 = """SELECT CASE ?
                                               WHEN 'stem' THEN stem
                                               WHEN 'lemma' THEN lemma
                                               ELSE text
                                               END word,
                                               pos,
                                               COUNT(DISTINCT document_id) AS count
                                        FROM string_tokens
                                        WHERE dataset_id = ?
                                        """
            update_count_sql2 = """) as counttable
                                       WHERE dataset_id = ?
                                       AND CASE ?
                                            WHEN 'stem' THEN stem
                                            WHEN 'lemma' THEN lemma
                                            ELSE text
                                       END = counttable.word
                                       AND string_tokens.pos = counttable.pos
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

            #apply rule
            field = rule[0]
            word = rule[1]
            pos = rule[2]
            action = rule[3]
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
        logger.info("Finished Applying Rule %s", str(rule))

    def RefreshStringTokensIncluded(self, dataset_key):
        logger = logging.getLogger(__name__+".RefreshStringTokensIncluded")
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
            sql_truncate_stringtokensincluded = """DELETE FROM string_tokens_included WHERE dataset_id = ?"""
            c.execute(sql_truncate_stringtokensincluded, (dataset_id,))
            sql_insert_stringtokensincluded = """INSERT INTO string_tokens_included (
                                                    dataset_id,
                                                    words,
                                                    pos, 
                                                    num_of_words,
                                                    num_of_docs,
                                                    spacy_stopword,
                                                    tfidf_range_min,
                                                    tfidf_range_max
                                                 )
                                                 SELECT
                                                    dataset_id,
                                                    CASE :token_type
                                                        WHEN 'stem' THEN stem
                                                        WHEN 'lemma' THEN lemma
                                                        ELSE text
                                                        END AS words,
                                                    pos,
                                                    COUNT(CASE :token_type
                                                            WHEN 'stem' THEN stem
                                                            WHEN 'lemma' THEN lemma
                                                            ELSE text
                                                            END) AS num_of_words,
                                                    COUNT(DISTINCT document_id) AS num_of_docs,
                                                    spacy_stopword,
                                                    CASE :token_type
                                                        WHEN 'stem' THEN ROUND(MIN(stem_tfidf),4)
                                                        WHEN 'lemma' THEN ROUND(MIN(lemma_tfidf),4)
                                                        ELSE ROUND(MIN(text_tfidf),4)
                                                        END AS tfidf_range_min,
                                                    CASE :token_type
                                                        WHEN 'stem' THEN ROUND(MAX(stem_tfidf),4)
                                                        WHEN 'lemma' THEN ROUND(MAX(lemma_tfidf),4)
                                                        ELSE ROUND(MAX(text_tfidf),4)
                                                        END AS tfidf_range_max
                                                 FROM string_tokens
                                                 WHERE dataset_id = :dataset_id
                                                 AND included = 1
                                                 GROUP BY dataset_id,
                                                          words,
                                                          pos,
                                                          spacy_stopword"""
            c.execute(sql_insert_stringtokensincluded, {'token_type': token_type, 'dataset_id': dataset_id})
            self.__conn.commit()
            c.close()
        except sqlite3.Error as e:
            logger.exception("sql failed with error")
        logger.info("Finished")
    
    def RefreshStringTokensRemoved(self, dataset_key):
        logger = logging.getLogger(__name__+".RefreshStringTokensRemoved")
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
            sql_truncate_stringtokensremoved = """DELETE FROM string_tokens_removed WHERE dataset_id = ?"""
            c.execute(sql_truncate_stringtokensremoved, (dataset_id,))
            sql_insert_stringtokensremoved = """INSERT INTO string_tokens_removed (
                                                    dataset_id,
                                                    words,
                                                    pos, 
                                                    num_of_words,
                                                    num_of_docs,
                                                    spacy_stopword,
                                                    tfidf_range_min,
                                                    tfidf_range_max
                                                 )
                                                 SELECT
                                                    dataset_id,
                                                    CASE :token_type
                                                        WHEN 'stem' THEN stem
                                                        WHEN 'lemma' THEN lemma
                                                        ELSE text
                                                        END AS words,
                                                    pos,
                                                    COUNT(CASE :token_type
                                                            WHEN 'stem' THEN stem
                                                            WHEN 'lemma' THEN lemma
                                                            ELSE text
                                                            END) AS num_of_words,
                                                    COUNT(DISTINCT document_id) AS num_of_docs,
                                                    spacy_stopword,
                                                    CASE :token_type
                                                        WHEN 'stem' THEN ROUND(MIN(stem_tfidf),4)
                                                        WHEN 'lemma' THEN ROUND(MIN(lemma_tfidf),4)
                                                        ELSE ROUND(MIN(text_tfidf),4)
                                                        END AS tfidf_range_min,
                                                    CASE :token_type
                                                        WHEN 'stem' THEN ROUND(MAX(stem_tfidf),4)
                                                        WHEN 'lemma' THEN ROUND(MAX(lemma_tfidf),4)
                                                        ELSE ROUND(MAX(text_tfidf),4)
                                                        END AS tfidf_range_max
                                                 FROM string_tokens
                                                 WHERE dataset_id = :dataset_id
                                                 AND included = 0
                                                 GROUP BY dataset_id,
                                                          words,
                                                          pos,
                                                          spacy_stopword"""
            c.execute(sql_insert_stringtokensremoved, {'token_type': token_type, 'dataset_id': dataset_id})
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
            sql_select_datasetid = """SELECT id, token_type
                                      FROM datasets 
                                      WHERE dataset_key = ?
                                      """
            c.execute(sql_select_datasetid, (str(dataset_key),))
            result = c.fetchone()
            dataset_id = result[0]
            token_type = result[1]

            sql_tokencount_query = """SELECT COUNT(*),
                                             CASE :token_type
                                                  WHEN 'stem' THEN COUNT(DISTINCT stem)
                                                  WHEN 'lemma' THEN COUNT(DISTINCT lemma)
                                                  ELSE COUNT(DISTINCT text)
                                                  END,
                                             COUNT(DISTINCT document_id)   
                                      FROM string_tokens
                                      WHERE dataset_id = :dataset_id
                                      """
            c.execute(sql_tokencount_query, {'dataset_id': dataset_id, 'token_type':token_type})
            cur_result = c.fetchone()
            counts['tokens'] = cur_result[0]
            counts['unique_tokens'] = cur_result[1]
            counts['documents'] = cur_result[2]

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
            sql_select_datasetid = """SELECT id, token_type
                                      FROM datasets 
                                      WHERE dataset_key = ?
                                      """
            c.execute(sql_select_datasetid, (str(dataset_key),))
            result = c.fetchone()
            dataset_id = result[0]
            token_type = result[1]

            sql_tokencount_query = """SELECT COUNT(*),
                                             CASE :token_type
                                                  WHEN 'stem' THEN COUNT(DISTINCT stem)
                                                  WHEN 'lemma' THEN COUNT(DISTINCT lemma)
                                                  ELSE COUNT(DISTINCT text)
                                                  END,
                                             COUNT(DISTINCT document_id)   
                                      FROM string_tokens
                                      WHERE dataset_id = :dataset_id
                                      AND included = 1
                                      """
            c.execute(sql_tokencount_query, {'dataset_id': dataset_id, 'token_type':token_type})
            cur_result = c.fetchone()
            counts['tokens'] = cur_result[0]
            counts['unique_tokens'] = cur_result[1]
            counts['documents'] = cur_result[2]

            c.close()
        except sqlite3.Error as e:
            logger.exception("sql failed with error")
        logger.info("Finished")
        return counts

    def GetIncludedStringTokens(self, dataset_key, word_search_term, pos_search_term, sort_col, sort_ascending):
        logger = logging.getLogger(__name__+".GetIncludedStringTokens")
        #logger.info("Starting")
        try:
            c = self.__conn.cursor()
            sql_select_datasetid = """SELECT id
                                      FROM datasets 
                                      WHERE dataset_key = ?
                                      """
            c.execute(sql_select_datasetid, (str(dataset_key),))
            dataset_id = c.fetchone()[0]

            sql_select_includedrow1 = """SELECT words,
                                                pos,
                                                num_of_words,
                                                num_of_docs,
                                                spacy_stopword,
                                                tfidf_range_min,
                                                tfidf_range_max
                                         FROM string_tokens_included
                                         WHERE dataset_id = ?
                                         """
            sql_select_includedrow2 = "ORDER BY "

            sql = sql_select_includedrow1 
            parameters = [dataset_id]
            if word_search_term != "":
                sql = sql + "AND words = ? "
                parameters.append(word_search_term)
            if pos_search_term != "":
                sql = sql + "AND pos = ? "
                parameters.append(pos_search_term)
            sql = sql + sql_select_includedrow2
            
            if sort_col is GUITextFiltering.FILTERS_WORDS:
                sql = sql + "words "
            elif sort_col is GUITextFiltering.FILTERS_POS:
                sql = sql + "pos "
            elif sort_col is GUITextFiltering.FILTERS_NUM_WORDS:
                sql = sql + "num_of_words "
            elif sort_col is GUITextFiltering.FILTERS_NUM_DOCS:
                sql = sql + "num_of_docs "
            elif sort_col is GUITextFiltering.FILTERS_SPACY_AUTO_STOPWORDS:
                sql = sql + "spacy_stopword "
            elif sort_col is GUITextFiltering.FILTERS_TFIDF_MAX:
                sql = sql + "tfidf_range_max "
            elif sort_col is GUITextFiltering.FILTERS_TFIDF_MIN:
                sql = sql + "tfidf_range_min "
            
            if sort_ascending:
                sql = sql + "ASC "
            else:
                sql = sql + "DESC "

            c.execute(sql, parameters)
            data = c.fetchall()
            c.close()
        except sqlite3.Error as e:
            logger.exception("sql failed with error")
        #logger.info("Finished")
        return data

    def GetRemovedStringTokens(self, dataset_key, word_search_term, pos_search_term, sort_col, sort_ascending):
        logger = logging.getLogger(__name__+".GetRemovedStringTokens")
        #logger.info("Starting")
        try:
            c = self.__conn.cursor()
            sql_select_datasetid = """SELECT id
                                      FROM datasets 
                                      WHERE dataset_key = ?
                                      """
            c.execute(sql_select_datasetid, (str(dataset_key),))
            dataset_id = c.fetchone()[0]

            sql_select_removedrow1 = """SELECT words,
                                               pos,
                                               num_of_words,
                                               num_of_docs,
                                               spacy_stopword,
                                               tfidf_range_min,
                                               tfidf_range_max
                                        FROM string_tokens_removed
                                        WHERE dataset_id = ?
                                        """
            sql_select_removedrow2 = "ORDER BY "

            sql = sql_select_removedrow1 
            parameters = [dataset_id]
            if word_search_term != "":
                sql = sql + "AND words = ? "
                parameters.append(word_search_term)
            if pos_search_term != "":
                sql = sql + "AND pos = ? "
                parameters.append(pos_search_term)
            sql = sql + sql_select_removedrow2
            
            if sort_col is GUITextFiltering.FILTERS_WORDS:
                sql = sql + "words "
            elif sort_col is GUITextFiltering.FILTERS_POS:
                sql = sql + "pos "
            elif sort_col is GUITextFiltering.FILTERS_NUM_WORDS:
                sql = sql + "num_of_words "
            elif sort_col is GUITextFiltering.FILTERS_NUM_DOCS:
                sql = sql + "num_of_docs "
            elif sort_col is GUITextFiltering.FILTERS_SPACY_AUTO_STOPWORDS:
                sql = sql + "spacy_stopword "
            elif sort_col is GUITextFiltering.FILTERS_TFIDF_MIN:
                sql = sql + "tfidf_range_min "
            elif sort_col is GUITextFiltering.FILTERS_TFIDF_MAX:
                sql = sql + "tfidf_range_max "

            if sort_ascending:
                sql = sql + "ASC "
            else:
                sql = sql + "DESC "

            c.execute(sql, parameters)
            data = c.fetchall()
            c.close()
        except sqlite3.Error as e:
            logger.exception("sql failed with error")
        #logger.info("Finished")
        return data

    def GetDocumentsTokensFromStringTokens(self, dataset_key):
        logger = logging.getLogger(__name__+".GetDocumentsTokensFromStringTokens")
        logger.info("Starting")
        tokens_dict = {}
        try:
            c = self.__conn.cursor()
            sql_select_datasetid = """SELECT id, token_type
                                      FROM datasets 
                                      WHERE dataset_key = ?
                                      """
            c.execute(sql_select_datasetid, (str(dataset_key),))
            result = c.fetchone()
            dataset_id = result[0]
            token_type = result[1]

            sql_select_documenttokens = """SELECT document_key,
                                                 GROUP_CONCAT(word, " ") 
                                           FROM (SELECT document_key,
                                                        CASE :token_type
                                                        WHEN 'stem' THEN stem
                                                        WHEN 'lemma' THEN lemma
                                                        ELSE text
                                                        END as word
                                                 FROM string_tokens
                                                 LEFT JOIN  documents ON
                                                    string_tokens.document_id = documents.id
                                                 WHERE string_tokens.dataset_id = :dataset_id
                                                 AND string_tokens.included = 1
                                                 ORDER BY string_tokens.document_id ASC,
                                                          string_tokens.field_id ASC,
                                                          string_tokens.position ASC)
                                           GROUP BY document_key
                                           """
            tokens_dict = {}
            c.execute(sql_select_documenttokens, {'dataset_id':dataset_id, 'token_type':token_type})
            for row in c.fetchall():
                tokens_dict[eval(row[0])] = row[1].split()
            c.close()
        except sqlite3.Error as e:
            logger.exception("sql failed with error")
        logger.info("Finished")
        return tokens_dict
