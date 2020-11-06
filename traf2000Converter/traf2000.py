#!/usr/bin/env python3

###### -*- coding: utf-8 -*-
import csv
import pprint
import unidecode

fatture = dict()

with open("./fatture.csv", newline="") as fileCsv:
    lettore = csv.reader(fileCsv, delimiter=",")
    header = next(lettore)
    for linea in lettore:
        numFattura = linea[1]
        if numFattura not in fatture:
            fattura = {
                "numFattura": numFattura,
                "tipoFattura": linea[8],
                "dataFattura": linea[2],
                "ragioneSociale": unidecode.unidecode(linea[6] + " " + " ".join(linea[5].split(" ")[0:2])),
                "posDivide": str(len(linea[6]) + 1),
                "cf": linea[7],
                "importoTotale": 0,
            }
            if linea[14] == "Ritenuta d'acconto":
                fattura["ritenutaAcconto"] = linea[15]
            else:
                fattura["righe"] = {linea[14]: linea[15]}
            fatture[numFattura] = fattura
        else:
            if linea[14] == "Ritenuta d'acconto":
                fatture[numFattura]["ritenutaAcconto"] = linea[15]
            else:
                fatture[numFattura]["righe"][linea[14]] = linea[15]
with open("./noteCredito", "w") as fileNC:
    fileNC.write("Note di credito\n")
with open("./TRAF2000", "w") as fileTxt:
    for fattura in fatture.values():
        if fattura["tipoFattura"] == "Nota di credito":
            with open("./noteCredito", "a") as fileNC:
                fileNC.write(fattura["numFattura"] + '\n')
            continue
        linea = ["04103", "3", "0", "00000"]  # TRF-DITTA + TRF-VERSIONE + TRF-TARC + TRF-COD-CLIFOR
        linea.append(fattura["ragioneSociale"][:32]+' '*(32-len(fattura["ragioneSociale"])))  # TRF-RASO
        linea.append(' '*30)  # TRF-IND
        linea.append('00000')  # TRF-CAP
        linea.append(' '*27)  # TRF-CITTA + TRF-PROV
        if len(fattura["cf"]) == 16:  # se c.f. presente
            linea.append(fattura["cf"])  # TRF-COFI
            linea.append('0'*11)  # TRF-PIVA
            linea.append('S')  # TRF-PF
        elif len(fattura["cf"]) == 11:  # se piva presente
            linea.append(' '*16)  # TRF-COFI
            linea.append(fattura["cf"])  # TRF-PIVA
            linea.append('N')  # TRF-PF
        else:
            print("Errore: no cf/piva")
        linea.append('0'*(2-len(fattura["posDivide"])) + fattura["posDivide"])  # TRF-DIVIDE
        linea.append('0000')  # TRF-PAESE
        linea.append(' '*33)  # TRF-PIVA-ESTERO + TRF-COFI-ESTERO + TRF-SESSO
        linea.append('0'*8)  # TRF-DTNAS
        linea.append(' '*64)  # TRF-COMNA + TRF-PRVNA + TRF-PREF + TRF-NTELE-NUM + TRF-FAX-PREF + TRF-FAX-NUM
        linea.append('0'*22)  # TRF-CFCONTO + TRF-CFCODPAG + TRF-CFBANCA + TRF-CFAGENZIA + TRF-CFINTERM
        if fattura["tipoFattura"] == "Fattura":
            linea.append('001')  # TRF-CAUSALE
            linea.append("FATTURA VENDITA")  # TRF-CAU-DES
        elif fattura["tipoFattura"] =="Nota di credito":
            linea.append('002')  # TRF-CAUSALE
            linea.append("NOTA DI CREDITO")  # TRF-CAU-DES
        linea.append(' '*86)  # TRF-CAU-AGG + TRF-CAU-AGG-1 + TRF-CAU-AGG-2
        linea.append(fattura["dataFattura"].replace("/", "")*2)  # TRF-DATA-REGISTRAZIONE + TRF-DATA-DOC
        linea.append('00000000')  # TRF-NUM-DOC-FOR
        linea.append(fattura["numFattura"][4:9])  # TRF-NDOC
        linea.append('00')  # TRF-SERIE
        linea.append('0'*72)  # TRF-EC-PARTITA + TRF-EC-PARTITA-ANNO + TRF-EC-COD-VAL + TRF-EC-CAMBIO + TRF-EC-DATA-CAMBIO + TRF-EC-TOT-DOC-VAL + TRF-EC-TOT-IVA-VAL + TRF-PLAFOND
        conta = 0
        for desc, imponibile in fattura["righe"].items():
            conta += 1
            imponibile = imponibile.replace("€", "").replace(",", "").replace(".", "").replace("(", "").replace(")", "")
            fattura["importoTotale"] += int(imponibile)
            imponibile = '0'*(11-len(imponibile)) + imponibile + "+"
            linea.append(imponibile)  # TRF-IMPONIB
            if desc != "Bollo":
                linea.append('308')  # TRF-ALIQ
            else:
                linea.append('315')  # TRF-ALIQ
            linea.append('0'*16)  # TRF-ALIQ-AGRICOLA + TRF-IVA11 + TRF-IMPOSTA
        for i in range(8-conta):
            linea.append('0'*31)
        totale = str(fattura["importoTotale"])
        totale = '0'*(11-len(totale)) + totale + "+"
        linea.append(totale)  # TRF-TOT-FAT
        conta = 0
        for desc, imponibile in fattura["righe"].items():
            conta += 1
            imponibile = imponibile.replace("€", "").replace(",", "").replace(".", "").replace("(", "").replace(")", "")
            imponibile = '0'*(11-len(imponibile)) + imponibile + "+"
            if desc != "Bollo":
                linea.append('4004300')  # TRF-CONTO-RIC
            else:
                linea.append('4004500')  # TRF-CONTO-RIC
            linea.append(imponibile)  # TRF-IMP-RIC
        for i in range(8-conta):
            linea.append('0'*19)

        linea.append('000')  # TRF-CAU-PAG
        linea.append(' '*83)  # TRF-CAU-DES-PAGAM + TRF-CAU-AGG-1-PAGAM + TRF-CAU-AGG-2-PAGAM
        linea.append(('0000000' + ' ' + '0'*12 + ' '*18 + '0'*26)*80)  # TRF-CONTO + TRF-DA + TRF-IMPORTO + TRF-CAU-AGGIUNT + TRF-EC-PARTITA-PAG + TRF-EC-PARTITA-ANNO-PAG + TRF-EC-IMP-VAL
        linea.append((' ' + '0'*18)*10)  # TRF-RIFER-TAB + TRF-IND-RIGA + TRF-DT-INI + TRF-DT-FIN
        linea.append('000000')  # TRF-DOC6
        linea.append('N' + '0')  # TRF-AN-OMONIMI + TRF-AN-TIPO-SOGG
        linea.append('00'*80)  # TRF-EC-PARTITA-SEZ-PAG
        linea.append('0'*15)  # TRF-NUM-DOC-PAG-PROF + TRF-DATA-DOC-PAG-PROF
        if "ritenutaAcconto" in fattura:
            imponibile = fattura["ritenutaAcconto"].replace("€", "").replace(",", "").replace("(", "").replace(")", "")
            imponibile = '0'*(11-len(imponibile)) + imponibile + "-"
            linea.append(imponibile)  # TRF-RIT-ACC
        else:
            linea.append('0'*12)  # TRF-RIT-ACC
        linea.append('0'*60)  # TRF-RIT-PREV + TRF-RIT-1 + TRF-RIT-2 + TRF-RIT-3 + TRF-RIT-4
        linea.append('00'*8)  # TRF-UNITA-RICAVI
        linea.append('00'*80)  # TRF-UNITA-PAGAM
        linea.append(' '*24)  # TRF-FAX-PREF-1 + TRF-FAX-NUM-1
        linea.append(' ' + ' ')  # TRF-SOLO-CLIFOR + TRF-80-SEGUENTE
        linea.append('0000000')  # TRF-CONTO-RIT-ACC
        linea.append('0'*35)   # TRF-CONTO-RIT-PREV + TRF-CONTO-RIT-1 + TRF-CONTO-RIT-2 + TRF-CONTO-RIT-3 + TRF-CONTO-RIT-4
        linea.append('N' + 'N' + '00000000' + '000')  # TRF-DIFFERIMENTO-IVA + TRF-STORICO + TRF-STORICO-DATA + TRF-CAUS-ORI
        linea.append(' ' + ' ' + '0'*16 + ' ')  # TRF-PREV-TIPOMOV + TRF-PREV-RATRIS + TRF-PREV-DTCOMP-INI + TRF-PREV-DTCOMP-FIN + TRF-PREV-FLAG-CONT
        linea.append(' '*20 + '0'*21 + ' '*44 + '0'*8 + ' ' + '0'*6 + ' ' + '00' + ' ')  # TRF-RIFERIMENTO + TRF-CAUS-PREST-ANA + TRF-EC-TIPO-PAGA + TRF-CONTO-IVA-VEN-ACQ + TRF-PIVA-VECCHIA + TRF-PIVA-ESTERO-VECCHIA + # TRF-RISERVATO + TRF-DATA-IVA-AGVIAGGI + TRF-DATI-AGG-ANA-REC4 + TRF-RIF-IVA-NOTE-CRED + TRF-RIF-IVA-ANNO-PREC + TRF-NATURA-GIURIDICA + TRF-STAMPA-ELENCO
        linea.append('000'*8 + ' '*20 + '0' + ' '*4 + '0'*6 + ' '*21 + 'N' + ' '*4 + 'S' + ' '*2)  # TRF-PERC-FORF + TRF-SOLO-MOV-IVA + TRF-COFI-VECCHIO + TRF-USA-PIVA-VECCHIA + TRF-USA-PIVA-EST-VECCHIA + TRF-USA-COFI-VECCHIO + TRF-ESIGIBILITA-IVA + TRF-TIPO-MOV-RISCONTI + TRF-AGGIORNA-EC + TRF-BLACKLIST-ANAG + TRF-BLACKLIST-IVA-ANNO + TRF-CONTEA-ESTERO + TRF-ART21-ANAG + TRF-ART21-IVA + TRF-RIF-FATTURA + TRF-RISERVATO-B + TRF-MASTRO-CF + TRF-MOV-PRIVATO + TRF-SPESE-MEDICHE + TRF-FILLER
        linea.append('\n')

        #RECORD 5 per Tessera Sanitaria
        linea.append('04103' + '3' + '5')  # TRF5-DITTA + TRF5-VERSIONE + TRF5-TARC
        linea.append(' '*1200)  # TRF-ART21-CONTRATTO
        linea.append('0'*6 + ' '*16)  # TRF-A21CO-ANAG + # TRF-A21CO-COFI  
        linea.append('0'*8 + ' ' + '000' + '00' + str(fattura["importoTotale"]) + '0'*14 + '0'*8 + ' '*40)  # TRF-A21CO-DATA + TRF-A21CO-FLAG + TRF-A21CO-ALQ + TRF-A21CO-IMPORTO + TRF-A21CO-IMPOSTA + TRF-A21CO-NDOC + TRF-A21CO-CONTRATTO
        linea.append(('0'*8 + ' ' + '000' + '0'*14 + '0'*14 + '0'*8 + ' '*40)*49)  # TRF-A21CO-DATA + TRF-A21CO-FLAG + TRF-A21CO-ALQ + TRF-A21CO-IMPORTO + TRF-A21CO-IMPOSTA + TRF-A21CO-NDOC + TRF-A21CO-CONTRATTO
        linea.append('0'*16)  # TRF-RIF-FATT-NDOC + TRF-RIF-FATT-DDOC
        linea.append(' ' + 'SR' + '2')  # TRF-A21CO-TIPO + TRF-A21CO-TIPO-SPESA + TRF-A21CO-FLAG-SPESA
        linea.append((' ' + '  ' + ' ')*50)  # TRF-A21CO-TIPO + TRF-A21CO-TIPO-SPESA + TRF-A21CO-FLAG-SPESA
        linea.append(' '*78)  # TRF-SPESE-FUNEBRI + FILLER + FILLER

        linea = ''.join(linea) + '\n'

        fileTxt.write(linea)

#pprint.pprint(fatture)