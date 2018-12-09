"""Read the database and write the PLC file"""
#!/usr/bin/python

import sys
import io
import re
import pymysql
import logging
logging.basicConfig(level=logging.WARNING)

try:
    import pyotherside
except:
    logging.info("loopCFG_createPLC.py: could not import pyotherside")


from openpyxl import *
from decode_tables import *
from collections import defaultdict

import collections

all_globals = defaultdict(list)


def set_bit(v, offset):
    mask = 1 << offset
    return v | mask


def main(sel_site):
    try:
        # Define our connection string
        conn = pymysql.connect(
            host="localhost",
            user="root",
            passwd="move",
            db="wtg")
        # trying multiple connections so I can query from different tables in
        # the same loop
        cur_cfg = conn.cursor()
        cur_drv_fp = conn.cursor()
        cur_wire = conn.cursor()
        try:
            pyotherside.send("Connected")
        except:
            print("Connected")
    except:
        try:
            pyotherside.send("I am unable to connect to the database")
        except:
            print("I am unable to connect to the database")
        raise
    # tempWord = 0b0000000000000010
    # tempWord = 0
    # format(tempWord, '016b')
    # print(set_bit(tempWord,0))
    # print(tempWord)
    # exit()
    List_of_IL = []
    try:
        pyotherside.send("Bulding PLC import file")
    except:
        logging.info("Bulding PLC import file")
    # statement = """SELECT * FROM cfg WHERE site like '%s'""" % (sel_site)
    statement = """SELECT * FROM cfg WHERE site like '%s' \
    ORDER BY offset """ % (sel_site)
    cur_cfg.execute(statement)
    cfg_records = cur_cfg.rowcount
    for i in range(0, cfg_records):
        row_cfg = cur_cfg.fetchone()
        drvfout = io.StringIO()
        if row_cfg:
            cfg = decode_cfg(row_cfg)
            if cfg.plc_name not in (None, 'None', '') and cfg.Valid:
                SX_IL = (
                    './ResultFiles/' +
                    sel_site +
                    '/sx_' +
                    cfg.plc_section +
                    '.IL')  # Name of the Txt file
                if not SX_IL in List_of_IL:
                    # print('Order is ',cfg.code)
                    List_of_IL.append(SX_IL)  # Creates a unique list of files
                    drvfout = open(SX_IL, "w")  # Create a CLEAN TXT file
                    drvfout.write('(*@PROPERTIES@ \n')
                    drvfout.write('TYPE: POU \n')
                    drvfout.write('LOCALE: 1033 \n')
                    drvfout.write('IEC_LANGUAGE: IL \n')
                    drvfout.write('PLC_TYPE: MICREXSX \n')
                    drvfout.write('PROC_TYPE: independent \n')
                    drvfout.write('*) \n')
                    drvfout.write(' ---------- Copyright - WTG Pty LTD ---\n')
                    drvfout.write('(* \n')
                    drvfout.write('\n')
                    drvfout.write('\n')
                    drvfout.write('PROGRAM ' + cfg.plc_section + '\n')
                    drvfout.write('\n')
                    drvfout.write('(*Group:Default*) \n')
                    drvfout.write('\n')
                    drvfout.write('VAR_EXTERNAL \n')
                    drvfout.write('\n')
    try:
        pyotherside.send("PLANT - Making the IO Section -- Fuji ---- ")
    except:
        logging.info("PLANT - Making the IO Section -- Fuji ---- ")
    # exit()

    # statement = """SELECT * FROM cfg WHERE site like '%s' """ % (sel_site)
    cur_cfg.execute(statement)
    cfg_records = cur_cfg.rowcount
    for i in range(0, cfg_records):
        row_cfg = cur_cfg.fetchone()
        drvfout = io.StringIO()
        if row_cfg:
            cfg = decode_cfg(row_cfg)
            # print('Order is ',cfg.offset,cfg.code)
            if cfg.plc_name not in (None, 'None', '') and cfg.Valid:
                #
                SX_IL = (
                    './ResultFiles/' +
                    sel_site +
                    '/sx_' +
                    cfg.plc_section +
                    '.IL')  # Name of the Txt file
                drvfout = open(SX_IL, "a")  # appends to the TXT file
                #
                #
                drv_fp_statement = """SELECT * FROM drv_fp WHERE S_C_T like '%s' ORDER BY offset """ % (cfg.S_C_T)
                cur_drv_fp.execute(drv_fp_statement)
                results = cur_drv_fp.fetchall()
                # - This section is to make a uniqure list as the fp can have mutliple entry
                drv_fp_TAGS = []
                for row_drv_fp in results:
                    if row_drv_fp:
                        drv_fp = decode_drv_fp(row_drv_fp)
                        if drv_fp.PLC_type in ('DI', 'DO', 'AI'):
                            if drv_fp_TAGS in (None, 'None', ''):
                                drv_fp_TAGS.append(drv_fp)
                            else:
                                #
                                er = len(drv_fp_TAGS)
                                flag_same_tag = False
                                for j in range(0, er):
                                    if drv_fp.plc_tag in drv_fp_TAGS[j].plc_tag:
                                        flag_same_tag = True
                                if not flag_same_tag:
                                    drv_fp_TAGS.append(drv_fp)
                #
                #if cfg.code == 'BLF1':
                    #print(len(drv_fp_TAGS))
                    #print(cur_drv_fp.rowcount)
                #
                er = len(drv_fp_TAGS)
                for j in range(0, er):
                    #
                    if drv_fp_TAGS[j].PLC_type == 'DI':
                        #
                        t_tag = drv_fp_TAGS[j].plc_tag
                        t_ref = drv_fp_TAGS[j].reference
                        t_str = ('   {0:25} : BOOL; (* {0:25} *) '.format(t_tag, t_ref))
                        drvfout.write(t_str + '\n')
                    if drv_fp_TAGS[j].PLC_type == 'DO':
                        t_tag = drv_fp_TAGS[j].plc_tag
                        t_ref = drv_fp_TAGS[j].reference
                        t_str = ('   {0:25} : BOOL; (* {0:25} *) '.format(t_tag, t_ref))
                    if drv_fp_TAGS[j].PLC_type == 'AI':
                        if drv_fp_TAGS[j].PLC_type == 'AI_750-455':
                            t_tag = drv_fp_TAGS[j].plc_tag
                            t_ref = drv_fp_TAGS[j].reference
                            t_str = ('   {0:25} : WORD; (* {0:25} *) '.format(t_tag, t_ref))
                        else:
                            t_tag = drv_fp_TAGS[j].plc_tag
                            t_ref = drv_fp_TAGS[j].reference
                            t_str = ('   {0:25} : INT; (* {0:25} *) '.format(t_tag, t_ref))
                # Place more global var that got generated from Function
                # Blocks
                # drvfout.write('\n')
                # print(cfg.plc_name)

                # Found that I want to print 1 tab in therefore do a lot of w

                #drvfout.write(cfg.plc_VAR_EX)
                if cfg.plc_VAR_EX not in (None, 'None', ''):
                    #
                    mylist = cfg.plc_VAR_EX.split('\n')
                    mylist_len = len(mylist)
                    for k in range(0, mylist_len):
                        if mylist[k] != '':
                            drvfout.write('        ' + mylist[k] + '\n')
                # drvfout.write('\n')
    #
    try:
        pyotherside.send(" PLANT - Placing the footer")
    except:
        logging.info(" PLANT - Placing the footer")
    k = len(List_of_IL)  # Length of the config File
    for cnt in range(0, k):
        SX_IL = List_of_IL[cnt]  # This is PLC File
        if len(SX_IL) > 0:
            drvfout = open(SX_IL, "a")  # Create a CLEAN TXT file
            drvfout.write('\n')
            drvfout.write('END_VAR \n')
            drvfout.write('\n')
            drvfout.write('VAR \n')
            drvfout.write('\n')
    try:
         pyotherside.send("PLANT - Making the Local Var Section")
    except:
        logging.info("PLANT - Making the Local Var Section")
    # statement = """SELECT * FROM cfg WHERE site like '%s' """ % (sel_site)
    cur_cfg.execute(statement)
    cfg_records = cur_cfg.rowcount
    for i in range(0, cfg_records):
        row_cfg = cur_cfg.fetchone()
        drvfout = io.StringIO()
        if row_cfg:
            cfg = decode_cfg(row_cfg)
            if cfg.plc_name not in (None, 'None', '') and cfg.Valid:
                # print('Code-',cfg.code,'Name',cfg.plc_name)
                #
                SX_IL = (
                    './ResultFiles/' +
                    sel_site +
                    '/sx_' +
                    cfg.plc_section +
                    '.IL')  # Name of the Txt file
                drvfout = open(SX_IL, "a")  # appends to the TXT file
                # drvfout.write('\n')
                # print(cfg.plc_name)
                # drvfout.write('        ' + cfg.plc_VAR)
                if cfg.plc_VAR not in (None, 'None', ''):
                    mylist = cfg.plc_VAR.split('\n')
                    mylist_len = len(mylist)
                    for k in range(0, mylist_len):
                        if mylist[k] != '':
                            drvfout.write('        ' + mylist[k] + '\n')
                    # drvfout.write('\n')
    try:
        pyotherside.send("PLANT - Placing the footer on the end of each File")
    except:
        logging.info("PLANT - Placing the footer on the end of each File")
    k = len(List_of_IL)  # Length of the config File
    for cnt in range(0, k):
        SX_IL = List_of_IL[cnt]  # This is PLC File
        if len(SX_IL) > 0:
            drvfout = open(SX_IL, "a")  # Create a CLEAN TXT file
            drvfout.write('\n')
            drvfout.write('END_VAR \n')
            drvfout.write('\n')
    try:
         pyotherside.send("PLANT - Generating the PLC Code-------- Fuji")
    except:
        logging.info("PLANT - Generating the PLC Code-------- Fuji")
    # statement = """SELECT * FROM cfg WHERE site like '%s' """ % (sel_site)
    cur_cfg.execute(statement)
    cfg_records = cur_cfg.rowcount
    for i in range(0, cfg_records):
        row_cfg = cur_cfg.fetchone()
        drvfout = io.StringIO()
        if row_cfg:
            cfg = decode_cfg(row_cfg)
            if cfg.plc_name not in (None, 'None', '') and cfg.Valid:
                #
                SX_IL = (
                    './ResultFiles/' +
                    sel_site +
                    '/sx_' +
                    cfg.plc_section +
                    '.IL')  # Name of the Txt file
                drvfout = open(SX_IL, "a")  # appends to the TXT file
                drvfout.write('\n')
                # drvfout.write('        ' + cfg.plc_IL)
                #
                if cfg.plc_IL not in (None, 'None', ''):
                    mylist = cfg.plc_IL.split('\n')
                    mylist_len = len(mylist)
                    for k in range(0, mylist_len):
                        if mylist[k] != '':
                            drvfout.write('        ' + mylist[k] + '\n')
                    drvfout.write('\n')

    try:
        pyotherside.send("PLANT - Placing the footer on the end of each File")
    except:
        logging.info("PLANT - Placing the footer on the end of each File")
    # Append END_PROGRAM to the IL OUTPUT
    k = len(List_of_IL)  # Length of the config File
    for cnt in range(0, k):
        SX_IL = List_of_IL[cnt]  # This is PLC File
        if len(SX_IL) > 0:
            drvfout = open(SX_IL, "a")  # Create a CLEAN TXT file
            drvfout.write('\n')
            drvfout.write('END_PROGRAM \n')
            drvfout.write('\n')

    # ----------------------------------------------------------
    # Make the setup file for the drives
    try:
        pyotherside.send("ST SetupFile - Placing the Header")
    except:
        logging.info("ST SetupFile - Placing the Header")
    List_of_IL = []
    SX_IL = (
        './ResultFiles/' +
        sel_site +
        '/sx_InitBasic.ST')  # Create a CLEAN TXT file
    if not SX_IL in List_of_IL:
        List_of_IL.append(SX_IL)  # Creates a unique list of files
        drvfout = open(SX_IL, "w")  # Create a CLEAN TXT file
        drvfout.write('(*@PROPERTIES@ \n')
        drvfout.write('TYPE: POU \n')
        drvfout.write('LOCALE: 1033 \n')
        drvfout.write('IEC_LANGUAGE: ST \n')
        drvfout.write('PLC_TYPE: MICREXSX \n')
        drvfout.write('PROC_TYPE: independent \n')
        drvfout.write('*) \n')
        drvfout.write('\n')
        drvfout.write('PROGRAM InitBasic \n')
        drvfout.write('\n')
        drvfout.write('VAR_EXTERNAL \n')
        drvfout.write('		First_Scan : BOOL;\n')
        drvfout.write('		One_Sec_Pls : BOOL;\n')
        drvfout.write('		All_Drv_XXX_CFG 	 : All_Drv_XXX_CFG;\n')
    #	drvfout.write('		All_Drv_XXX_Leg  	 : All_Drv_XXX_Leg;\n')
        drvfout.write('\n')
        drvfout.write('END_VAR \n')
        drvfout.write('\n')
        drvfout.write('VAR \n')
        drvfout.write('\n')
        drvfout.write('\n')
        drvfout.write('END_VAR \n')
        drvfout.write('\n')
        drvfout.write('IF NOT(First_Scan) THEN RETURN; END_IF; \n')
        drvfout.write('First_Scan := FALSE; \n')
        drvfout.write('\n')

    # Done during Creation
    # cfg_IN1_TYPE_Status   : BOOL;  Input 1 Type Status Only no control
    # cfg_IN1_TYPE_Fatal    : BOOL;  Input 1 Type Will cause Drive to Fault
    # cfg_IN1_TYPE_Warning  : BOOL;  Input 1 Type Will indicate warning on ICON
    # cfg_IN1_TYPE_Fatal_PT : BOOL;  Input 1 Type Fatal plus Time
    # cfg_IN1_Flag_Invert   : BOOL;  The signal is inverted eg high is health
    # for fault, etc
    try:
        pyotherside.send("Building the Code for")
    except:
        logging.info("Building the Code for")
    arry_cfg_word = defaultdict(list)
    # statement = """SELECT * FROM cfg WHERE site like '%s' """ % (sel_site)
    cur_cfg.execute(statement)
    cfg_records = cur_cfg.rowcount
    for i in range(0, cfg_records):
        row_cfg = cur_cfg.fetchone()
        drvfout = io.StringIO()
        if row_cfg:
            cfg = decode_cfg(row_cfg)
            if cfg.plc_name not in (None, 'None', '') and cfg.Valid:
                #
                drvfout = open(
                    './ResultFiles/' +
                    sel_site +
                    '/sx_InitBasic.ST',
                    "a")  # appends to the TXT file
                if cfg.flag_bin == 1:
                    drvfout.write(
                        '   ALL_Drv_XXX_CFG[' + str(cfg.offset) + '].Flag_bin\
                         := TRUE; (* ' + cfg.code + ' *) \n')
                if cfg.flag_SC == 1:
                    drvfout.write(
                        '   ALL_Drv_XXX_CFG['
                        + str(cfg.offset) + '].Flag_Source := TRUE; \
                        (* ' + cfg.code + ' *) \n')
                if cfg.flag_DC == 1:
                    drvfout.write(
                        '   ALL_Drv_XXX_CFG[' + str(cfg.offset) + '].Flag_Dest\
                         := TRUE; (* ' + cfg.code + ' *) \n')

                drv_fp_statement = """SELECT * FROM drv_fp WHERE S_C_T like\
                 '%s' ORDER BY offset """ % (cfg.S_C_T)
                cur_drv_fp.execute(drv_fp_statement)
                drv_fp_records = cur_drv_fp.rowcount
                for j in range(0, drv_fp_records):
                    row_drv_fp = cur_drv_fp.fetchone()
                    if row_drv_fp:
                        drv_fp = decode_drv_fp(row_drv_fp)
                        if drv_fp.PLC_type == 'DI' and drv_fp.flag_fatal:
                            # drvfout.write('   ALL_Drv_XXX_CFG[' +
                            # str(cfg.offset) + '].cfg_IN' +
                            # str(drv_fp.fp_ref_bit + 1) + '_TYPE_Fatal :=
                            # TRUE; (* ' + cfg.code + ' *) \n')
                            arry_cfg_word[cfg.offset].append(drv_fp.fp_ref_bit)

    #	 len(arry_cfg_word) == 0:
    #	arry_cfg_word[cfg.code].append(cfg.code)
    #	else:
    #	if not arry_cfg_word[cfg.code]:
    # arry_cfg_word[cfg.code].append(cfg.code)
    #		tempWord = 0b000
    #arry_cfg_word[cfg.code].append(set_bit(tempWord, int(drv_fp.fp_ref_bit)))
    #	lse:
    #	tempWord = arry_cfg_word[cfg.code]
    #				NewtempWord = 0b000
    # NewtempWord = set_bit(tempWord, int(drv_fp.fp_ref_bit))
    #		arry_cfg_word[cfg.code] = tempWord

    for s in arry_cfg_word.keys():
        # print('offset',s)
        tempWord = 0b0000000000000000
        er = len(arry_cfg_word[s])
        for n in range(0, er):
            #
            bit = arry_cfg_word[s][n]
            # print('       bit =',bit)
            tempWord = set_bit(tempWord, bit)
            change_tempWord = str(hex(tempWord)[2:])
        drvfout.write('   ALL_Drv_XXX_CFG[' + str(s) + '].Int_FATAL_MASK1\
         := WORD#16#' + change_tempWord + '; \n')
        # print(tempWord)
    try:
        pyotherside.send("Placing the footer on the end of each File")
    except:
        logging.info("Placing the footer on the end of each File")
    k = len(List_of_IL)  # Length of the config File
    for cnt in range(0, k):
        SX_IL = List_of_IL[cnt]  # This is PLC File
        if len(SX_IL) > 0:
            drvfout = open(SX_IL, "a")  # Create a CLEAN TXT file
            drvfout.write('\n')
            drvfout.write('END_PROGRAM \n')
            drvfout.write('\n')

    drvfout.write('\n')

    # --------------------------------------------------------------------------
    # --------------------------------------------------------------------------
    # --------------------------------------------------------------------------
    # --------------------------------------------------------------------------
    # --------------------------------------------------------------------------
    # --------------------------------------------------------------------------
    # - Do Sim Sections
    try:
        pyotherside.send("SIMULATION - Placing the Header on the sim section")
    except:
        logging.info("SIMULATION - Placing the Header on the sim section")
    # This make the IO sections First
    SX_IL = ('./ResultFiles/' + sel_site + '/sx_SimBasic.ST')  # CLEAN TXT file
    drvfout = open(SX_IL, "w")  # Create a CLEAN TXT file
    drvfout.write('(*@PROPERTIES@ \n')
    drvfout.write('TYPE: POU \n')
    drvfout.write('LOCALE: 1033 \n')
    drvfout.write('IEC_LANGUAGE: ST \n')
    drvfout.write('PLC_TYPE: MICREXSX \n')
    drvfout.write('PROC_TYPE: independent \n')
    drvfout.write('*) \n')
    drvfout.write('\n')
    drvfout.write('PROGRAM SimBasic \n')
    drvfout.write('\n')
    drvfout.write('VAR_EXTERNAL \n')
    drvfout.write('		First_Scan : BOOL;\n')
    drvfout.write('		One_Sec_Pls : BOOL;\n')
    drvfout.write('\n')

    wirelist_statement = """SELECT * FROM wirelist WHERE site = '%s' """ % (
        sel_site)
    cur_wire.execute(wirelist_statement)
    wirelist_records = cur_wire.rowcount
    for k in range(0, wirelist_records):
        row_wire = cur_wire.fetchone()
        if row_wire:
            wire = decode_wirelist(row_wire)
            if wire.plc_tag not in (None, 'None', ''):
                if re.search('DI', wire.card_type):
                    if wire.plc_tag not in all_globals:
                        all_globals[wire.plc_tag].append('BOOL')
                        all_globals[wire.plc_tag].append(wire.reference)
                if re.search('DO', wire.card_type):
                    if wire.plc_tag not in all_globals:
                        all_globals[wire.plc_tag].append('BOOL')
                        all_globals[wire.plc_tag].append(wire.reference)
                if re.search('AI', wire.card_type):
                    if wire.plc_tag not in all_globals:
                        if wire.card_type == 'AI_750-455':
                            all_globals[wire.plc_tag].append('WORD')
                            all_globals[wire.plc_tag].append(wire.reference)
                        else:
                            all_globals[wire.plc_tag].append('INT')
                            all_globals[wire.plc_tag].append(wire.reference)

    drvfout = open(SX_IL, "a")  # appends to the TXT file
    all_globals_sorted = collections.OrderedDict(sorted(all_globals.items()))
    for s in list(all_globals_sorted.keys()):
        t_tg = s  # ---------------------------- PLC TAG
        t_ty = all_globals_sorted[s][0]  # ----- type eg BOOL, INT, REAL
        t_co = all_globals_sorted[s][1]  # ----- Comment
        drvfout.write('      ' + t_tg + ':' + t_ty + '; (* ' + t_co + ' *) \n')
    #
    #
    drvfout = open(SX_IL, "a")  # Create a CLEAN TXT file
    drvfout.write('\n')
    drvfout.write('END_VAR \n')
    drvfout.write('\n')
    drvfout.write('VAR \n')
    drvfout.write('\n')
    #
    # statement = """SELECT * FROM cfg WHERE site like '%s' """ % (sel_site)
    cur_cfg.execute(statement)
    cfg_records = cur_cfg.rowcount
    for i in range(0, cfg_records):
        row_cfg = cur_cfg.fetchone()
        drvfout = io.StringIO()
        if row_cfg:
            cfg = decode_cfg(row_cfg)
            if cfg.plc_name not in (None, 'None', '') and cfg.Valid:
                # print('Code-',cfg.code,'Name',cfg.plc_name)
                #
                drvfout = open(SX_IL, "a")  # appends to the TXT file
                # drvfout.write('\n')
                # print(cfg.plc_name)
                # drvfout.write('        ' + cfg.plc_VAR)
                try:
                    mylist = cfg.plc_SimVAR.split('\n')
                except:
                    mylist = []
                #mylist = cfg.plc_SimVAR.split('\n')
                mylist_len = len(mylist)
                for k in range(0, mylist_len):
                    if mylist[k] != '':
                        drvfout.write('        ' + mylist[k] + '\n')
                # drvfout.write('\n')
    drvfout.write('END_VAR \n')
    try:
        pyotherside.send("PLANT - Generating the PLC Code--------------- Fuji")
    except:
        logging.info("PLANT - Generating the PLC Code--------------- Fuji")
    # statement = """SELECT * FROM cfg WHERE site like '%s' """ % (sel_site)
    cur_cfg.execute(statement)
    cfg_records = cur_cfg.rowcount
    for i in range(0, cfg_records):
        row_cfg = cur_cfg.fetchone()
        drvfout = io.StringIO()
        if row_cfg:
            cfg = decode_cfg(row_cfg)
            if cfg.plc_Sim is not None:
                drvfout = open(SX_IL, "a")  # appends to the TXT file
                drvfout.write('\n')
                drvfout.write(cfg.plc_Sim)
                drvfout.write('\n')
    try:
        pyotherside.send("PLANT - Placing the footer on the end of each File")
    except:
        logging.info("PLANT - Placing the footer on the end of each File")
    # Append END_PROGRAM to the IL OUTPUT
    drvfout = open(SX_IL, "a")  # Create a CLEAN TXT file
    drvfout.write('\n')
    drvfout.write('END_PROGRAM \n')
    drvfout.write('\n')

    # Write Basic SimCode ----------------------------------------------------
    # Write Basic SimCode ----------------------------------------------------

    # for key, value in arry_cfg_word.items():
    #	print (key, value)

    #
    # tempWord = 0
    # format(tempWord, '016b')
    # print(set_bit(tempWord,0))
    # print(tempWord)

    conn.close()
    try:
        pyotherside.send('complete')
    except:
        print('complete')


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        try:
            pyotherside.send('No Site Selected')
        except:
            print('No Site Selected')
        exit()
