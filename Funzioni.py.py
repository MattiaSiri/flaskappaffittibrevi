from flask_app import db, Reservation
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from socket import gethostname
from sqlalchemy import event
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound
from datetime import datetime, timedelta


##CALCOLARE TOTALE LORDO ANNO IN CORSO
def calcola_totale_lordo_anno_in_corso():
    # Imposta la data di inizio dell'anno (31/10)
    mese_corrente = datetime.today().month
    if mese_corrente >= 1 and mese_corrente <= 10:
        inizio_anno = datetime(datetime.today().year - 1, 10, 31)
    elif  mese_corrente==11 or mese_corrente==12: 
        inizio_anno = datetime(datetime.today().year , 10, 31)

    # Esegue la query per ottenere il totale_lordo delle prenotazioni di quest'anno
    totale_lordo_annuale = db.session.query(func.sum(Reservation.totale_lordo)).filter(
        Reservation.data_checkin >= inizio_anno,
        Reservation.data_checkin < inizio_anno+timedelta(days=365)
    ).scalar()
    # Se non ci sono prenotazioni, imposta il totale a 0
    totale_lordo_annuale = totale_lordo_annuale or 0
    
    return totale_lordo_annuale

##CALCOLARE TOTALE LORDO ANNO PRECEDENTE
def calcola_totale_lordo_anno_precedente():
    # Imposta la data di inizio dell'anno (31/10)
    mese_corrente = datetime.today().month
    if mese_corrente >= 1 and mese_corrente <= 10:
        inizio_anno = datetime(datetime.today().year - 2, 10, 31)
    elif  mese_corrente==11 or mese_corrente==12: 
        inizio_anno = datetime(datetime.today().year -1, 10, 31)

    # Esegue la query per ottenere il totale_lordo delle prenotazioni di quest'anno
    totale_lordo_annuale = db.session.query(func.sum(Reservation.totale_lordo)).filter(
        Reservation.data_checkin >= inizio_anno,
        Reservation.data_checkin < inizio_anno+timedelta(days=365)
    ).scalar()
    # Se non ci sono prenotazioni, imposta il totale a 0
    totale_lordo_annuale = totale_lordo_annuale or 0
    
    return totale_lordo_annuale

