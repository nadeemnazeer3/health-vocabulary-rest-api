from umls.models import MRCONSO
from umls.models import MRREL
from umls.models import ISA,ISA_RB
from umls.models import MRHIER
from umls.utils import get_cui
from umls.utils import get_code
from django.db import connection


class CodeResource:

    """ The Terminology Code resource """

    def _get(self, vocab, code_val):
        terms = MRCONSO.objects.filter(SAB=vocab, CODE=code_val)
        rterms = []
        for term in terms:
            rterms.append({
                'term': term.SAB,
                'code': term.CODE,
                'name': term.STR,
                'umls_cui': term.CUI,
                #'is_preferred':term.ISPERF
            })

        return rterms

    def _get_code(self, code, sab):

        if sab:
            sablist = sab.split(',')
            terms = MRCONSO.objects.filter(CODE=code).filter(SAB__in=sablist)
        else:
            terms = MRCONSO.objects.filter(CODE=code)

        rterms = []

        for term in terms:
            rterms.append({
                'code': term.CODE,
                'sab': term.SAB,
                'cuis': term.CUI,
                'str': term.STR,
            })

        return rterms

    def _get_code_det(self, code, sab):

        terms = MRCONSO.objects.filter(CODE=code, SAB=sab)

        rterms = []

        for term in terms:
            rterms.append({
                'code': term.CODE,
                'sab': term.SAB,
                'cuis': term.CUI,
                'str': term.STR,
            })

        return rterms


class RelResource:

    """ The Terminology Relationship resource """

    def _get(self, vocab, code_val, rel_type):

        source_cui = get_cui(vocab, code_val)

        rels_list = []
        if source_cui:
            rels = MRREL.objects.filter(CUI1=source_cui, RELA=rel_type)
            for rel in rels:
                rels_list.append({
                    'umls_cui': rel.CUI2,
                    'code': get_code(rel.SAB, rel.CUI2),
                    'rel': rel.REL,
                    'rela': rel.RELA
                })

        return rels_list


class MapResource:

    """ The Terminology Mapping resource """

    def _get(self, source_vocab, code_val, target_vocab):

        cui = get_cui(source_vocab, code_val)

        terms = MRCONSO.objects.filter(CUI=cui, SAB=target_vocab)
        rterms = []
        for term in terms:
            rterms.append({
                'target_vocab': term.SAB,
                'code': term.CODE,
                'name': term.STR,
            })

        return rterms


class ConceptResource:

    """ The Concept Resource """

    def _get(self, cui):

        cursor = connection.cursor()

        query = """SELECT CUI,
                      GROUP_CONCAT(DISTINCT STR SEPARATOR '|') as terms,
                      GROUP_CONCAT(DISTINCT SAB SEPARATOR '|') as sabs,
                      GROUP_CONCAT(ISPREF SEPARATOR '|') as is_prefs
                      FROM MRCONSO WHERE CUI=%s AND LAT='ENG' """

        cursor.execute(query, [cui])

        row = cursor.fetchone()
        if row:
            return {
                'cui': row[0],
                'terms': row[1].split("|"),
                'sabs': row[2].split("|"),
                # TODO get the pref term
            }

        return None

    def _get_synonyms(self, cui, sab):
        """ Get all synonyms of a cui from a SAB """

        if sab:
            sablist = sab.split(',')
            print sablist
            terms = MRCONSO.objects.filter(CUI=cui).filter(SAB__in=sablist)
        else:
            terms = MRCONSO.objects.filter(CUI=cui)
        rterms = []
        for term in terms:
            rterms.append(term.STR)
        return rterms


class ConceptListResource:

    """ Return a list of concepts """

    def _get(self, str, sabs, partial=False):

        cursor = connection.cursor()

        query_base = """SELECT CUI,
                      GROUP_CONCAT(DISTINCT STR SEPARATOR '|') as terms,
                      GROUP_CONCAT(DISTINCT SAB SEPARATOR '|') as sabs,
                      GROUP_CONCAT(ISPREF SEPARATOR '|') as is_prefs
                      FROM MRCONSO WHERE """
        query = query_base
        if sabs:
            query += " SAB IN (%(sabs)s) AND "

        if partial:
            query += " CONVERT(STR using latin1) LIKE %(str)s "
        else:
            query += " CONVERT(STR using latin1) = %(str)s "

        query += " GROUP BY CUI"  # since we need "Concept" objects

        cursor.execute(query, {"sabs": sabs,
                               "str": str})
        rterms = []

        for row in cursor.fetchall():
            rterms.append({
                'cui': row[0],
                'terms': row[1].split("|"),
                'sabs': row[2].split("|"),
                # TODO get the pref term
            })

        return rterms

    def _get_children(self, cui, sab, explode=False):
        """ Get childrens of a given cui

            Parameters:
                    cui: concept
                    sab: terminology to restrict the hierarchy
                    explode: if true, get recursively all children
            Returns:
                    List of Concept objects
        """
        cursor = connection.cursor()

        if explode:
            return self._get_exploded_hierarchy(cui, sab, "PAR")

        query = """SELECT
                    rel.cui2 as CUI
                    FROM `MRREL` rel
                    WHERE
                        rel.cui1 = %s  AND
                        rel.rel in ('CHD','RN')
                        """
        if sab:
            query += " AND rel.sab = %s  "
            cursor.execute(query, [cui, sab])
        else:
            cursor.execute(query, [cui])

        rterms = []

        cresource = ConceptResource()
        for row in cursor.fetchall():
            rterms.append(cresource._get(cui=row[0]))

        return rterms

    def _get_parent(self, cui, sab, explode=False):
        """ Get parents of a given cui

            Parameters:
                    cui: concept
                    sab: terminology to restrict the hierarchy
                    explode: if true, get recursively all parents
            Returns:
                    List of Concept objects
        """

        cursor = connection.cursor()

        if explode:
            return self._get_exploded_hierarchy(cui, sab, "CHD")

        query = """SELECT
                    rel.cui2 as CUI
                    FROM `MRREL` rel
                    WHERE
                        rel.cui1 = %s  AND
                        rel.rel in ('PAR','RB')
                        """
        if sab:
            query += " AND rel.sab = %s  "
            cursor.execute(query, [cui, sab])
        else:
            cursor.execute(query, [cui])

        rterms = []

        cresource = ConceptResource()
        for row in cursor.fetchall():
            rterms.append(cresource._get(cui=row[0]))

        return rterms

    def _get_exploded_hierarchy(self, cui, sab, direction):
        """ Get exploded hierarchy
                cui: concept hierarchy
                sab: source vocab to limit the hierarchy
                direction: CHD/PAR - get childrens or parents
        """

        print "EXPLODED"
        if direction == "CHD":
            isas = ISA.objects.filter(PARENT_CUI=cui)
        else:
            isas = ISA.objects.filter(CHILD_CUI=cui)
        if sab:
            isas = isas.filter(SAB=sab)

        rconcepts = []
        cresource = ConceptResource()
        for isa in isas:
            if direction == "CHD":
                rconcepts.append(cresource._get(isa.CHILD_CUI))
            else:
                rconcepts.append(cresource._get(isa.PARENT_CUI))

        # RB relationships
        if direction == "CHD":
            isas_rb = ISA_RB.objects.filter(PARENT_CUI=cui)
        else:
            isas_rb = ISA_RB.objects.filter(CHILD_CUI=cui)
        if sab:
            isas_rb = isas_rb.filter(SAB=sab)

        for isa in isas_rb:
            if direction == "CHD":
                rconcepts.append(cresource._get(isa.CHILD_CUI))
            else:
                rconcepts.append(cresource._get(isa.PARENT_CUI))
        return rconcepts

class HiersResource:
    pass

    """ The HIER Resource """

    def _get_hier(self, cui, sab):
        """ Get HIERS of a cui from a SAB """
        cursor = connection.cursor()

        query_base = """SELECT PTR,AUI,SAB
                      FROM MRHIER WHERE CUI='%s'"""%cui
        query = query_base

        if sab:
            query += "AND SAB ='%s'"%sab

        cursor.execute(query)
        rhiers = []
        sab_dict={}
        for row in cursor.fetchall():
            # print MRCONSO.objects.get(AUI=row[1]).STR
            key = row[2]
            if key not in sab_dict:
                sab_dict[key] = [row[0]+"."+row[1]]
            else:
                ls = sab_dict[key]
                ls.append(row[0]+"."+row[1])
                sab_dict[key] = ls
                # sab_dict[key].extend(row[0]+"."+row[1])
            rhiers.append(row[0]+"."+row[1])
        print sab_dict
        aui_dict = {}
        hier_list = []
        for key,ls in sab_dict.items():
            hier_list = []
            for item in ls:
                hier = ""
                auis = item.split('.')
                for aui in auis:
                    if aui not in aui_dict:
                        aui_dict[aui] = MRCONSO.objects.get(AUI=aui).STR
                    hier = hier+" => "+aui_dict[aui]
                hier_list.append(hier[4:])
            sab_dict[key] = hier_list

        # print hier_list

        return sab_dict


    #     cui_parent_list = {}
    #     for key,cui_list in cui_dict.items():
    #         cui_parent_list[key] = []
    #         for item in cui_list:
    #             par_list = clresource._get_parent(item['cui'],sab,True)
    #             for cui in par_list:
    #                 for top in cuis_top:
    #                     if top['cui'] == cui['cui']:
    #                         if key in cui_parent_list:
    #                             cui_parent_list[key].append(top['terms'][0])
    #                         else:
    #                             cui_parent_list[key] = [top['terms'][0]]
        
    #     mesh_top = {}
    #     for key,value in cui_parent_list.items():
    #         mesh_top[key] = list(set(value))

    #     return mesh_top