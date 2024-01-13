from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from socket import gethostname
from sqlalchemy import event
from sqlalchemy import func, extract
from sqlalchemy.orm.exc import NoResultFound
from datetime import datetime, timedelta
from collections import defaultdict
from flask_migrate import Migrate
from flask import jsonify



app = Flask(__name__)

# Configurazione per il database principale
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///main.db'
app.config['SQLALCHEMY_BINDS'] = {'finance': 'sqlite:///finance.db'}
db = SQLAlchemy(app)
migrate = Migrate(app, db)
app.secret_key = 'una_chiave_segreta_e_unica'

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_prenotazione = db.Column(db.Date, nullable=False)
    immobile = db.Column(db.String(50), nullable=False)
    portale = db.Column(db.String(50), nullable=False)
    numero = db.Column(db.String(50), nullable=False)
    nome_cognome = db.Column(db.String(100), nullable=False)
    numero_telefono = db.Column(db.String(15), nullable=False)
    data_checkin = db.Column(db.Date, nullable=False)
    data_checkout = db.Column(db.Date, nullable=False)
    numero_ospiti = db.Column(db.Integer, nullable=False)
    totale_lordo = db.Column(db.Float, nullable=False)
    no_tax = db.Column(db.Float, nullable=False)
    commissioni = db.Column(db.Float, nullable=False)
    stato = db.Column(db.String(15), nullable=False, default='In attesa')
    
    def __repr__(self):
        return f"<Reservation {self.nome} - {self.data_prenotazione} - {self.numero_persone}>"
    
    def as_dict(self):
        return {
            'id': self.id,
            'data_prenotazione': str(self.data_prenotazione),
            'immobile': self.immobile,
            'portale': self.portale,
            'numero': self.numero,
            'nome_cognome': self.nome_cognome,
            'numero_telefono': self.numero_telefono,
            'data_checkin': str(self.data_checkin),
            'data_checkout': str(self.data_checkout),
            'numero_ospiti': self.numero_ospiti,
            'totale_lordo': self.totale_lordo,
            'no_tax': self.no_tax,
            'commissioni': self.commissioni,
            'stato': self.stato,
        }

def get_reservations_sorted_by_checkin():
    # Restituisci le prenotazioni ordinate per data di check-in in ordine decrescente
    return Reservation.query.order_by(Reservation.data_checkin.desc()).all()

class Finance(db.Model):
    __bind_key__ = 'finance'
    id = db.Column(db.Integer, primary_key=True)
    data_scadenza = db.Column(db.Date, nullable=False)
    immobile = db.Column(db.String(50), nullable=False)
    portale = db.Column(db.String(50), nullable=False)
    soggetto = db.Column(db.String(50), nullable=False)
    descrizione = db.Column(db.String(100), nullable=False)
    importo = db.Column(db.Float, nullable=False)
    data_pagamento = db.Column(db.Date, nullable=True)
    conto = db.Column(db.String(15), nullable=False)
    stato = db.Column(db.String(15), nullable=False)
        
    def as_dict(self):
        return {
            'id': self.id,
            'data_scadenza': str(self.data_scadenza),
            'immobile': self.immobile,
            'portale': self.portale,
            'soggetto': self.soggetto,
            'descrizione': self.descrizione,
            'importo': self.importo,
            'data_pagamento': str(self.data_pagamento),
            'conto': self.conto,
            'stato': self.stato
        }

def get_reservations_sorted_by_scad():
    # Restituisci le prenotazioni ordinate per data di check-in in ordine decrescente
    return Finance.query.order_by(Finance.data_scadenza.desc()).all()

with app.app_context():
    db.create_all()

##--------------FUNZIONI-----------------

def get_check_ins_in_next_7_days():
    today = datetime.now()
    next_7_days = [today + timedelta(days=i) for i in range(7)]

    check_ins_data = []
    total_check_ins = 0  # Aggiunto per tenere traccia del totale dei check-in

    for day in next_7_days:
        check_ins_count = Reservation.query.filter(
            db.func.date(Reservation.data_checkin) == day.date()
        ).count()

        check_ins_data.append((str(day.date()), check_ins_count))
        total_check_ins += check_ins_count  # Aggiunto per incrementare il totale

    return total_check_ins



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

#calcolo numero di notti totali quest'anno
def calcola_totale_giorni_anno_in_corso():
    mese_corrente = datetime.today().month
    if mese_corrente >= 1 and mese_corrente <= 10:
        inizio_anno = datetime(datetime.today().year - 1, 10, 31).date()
    elif mese_corrente == 11 or mese_corrente == 12:
        inizio_anno = datetime(datetime.today().year, 10, 31).date()
    fine_anno = inizio_anno + timedelta(days=365)

    prenotazioni = Reservation.query.filter(
        Reservation.data_checkin >= inizio_anno,
        Reservation.data_checkin < fine_anno
    ).all()

    totale_giorni = 0

    for prenotazione in prenotazioni:
        durata_prenotazione = (prenotazione.data_checkout - prenotazione.data_checkin).days
        totale_giorni += durata_prenotazione

    return totale_giorni

#calcolo numero di notti totali anno precedente
def calcola_totale_giorni_anno_precedente():
    mese_corrente = datetime.today().month
    if mese_corrente >= 1 and mese_corrente <= 10:
        inizio_anno = datetime(datetime.today().year - 2, 10, 31).date()
    elif mese_corrente == 11 or mese_corrente == 12:
        inizio_anno = datetime(datetime.today().year - 1, 10, 31).date()
    fine_anno = inizio_anno + timedelta(days=365)

    prenotazioni = Reservation.query.filter(
        Reservation.data_checkin >= inizio_anno,
        Reservation.data_checkin < fine_anno
    ).all()

    totale_giorni = 0

    for prenotazione in prenotazioni:
        durata_prenotazione = (prenotazione.data_checkout - prenotazione.data_checkin).days
        totale_giorni += durata_prenotazione

    return totale_giorni

##CALCOLARE TOTALE COMMISSIONI ANNO IN CORSO
def calcola_totale_commissioni_anno_in_corso():
    # Imposta la data di inizio dell'anno (31/10)
    mese_corrente = datetime.today().month
    if mese_corrente >= 1 and mese_corrente <= 10:
        inizio_anno = datetime(datetime.today().year - 1, 10, 31)
    elif  mese_corrente==11 or mese_corrente==12: 
        inizio_anno = datetime(datetime.today().year , 10, 31)

    # Esegue la query per ottenere il totale_lordo delle prenotazioni di quest'anno
    totale_lordo_annuale = db.session.query(func.sum(Reservation.commissioni)).filter(
        Reservation.data_checkin >= inizio_anno,
        Reservation.data_checkin < inizio_anno+timedelta(days=365)
    ).scalar()
    # Se non ci sono prenotazioni, imposta il totale a 0
    totale_lordo_annuale = totale_lordo_annuale or 0
    
    return totale_lordo_annuale

##CALCOLARE TOTALE COMMISSIONI ANNO PRECEDENTE
def calcola_totale_commissioni_anno_precedente():
    # Imposta la data di inizio dell'anno (31/10)
    mese_corrente = datetime.today().month
    if mese_corrente >= 1 and mese_corrente <= 10:
        inizio_anno = datetime(datetime.today().year - 2, 10, 31)
    elif  mese_corrente==11 or mese_corrente==12: 
        inizio_anno = datetime(datetime.today().year -1, 10, 31)

    # Esegue la query per ottenere il totale_lordo delle prenotazioni di quest'anno
    totale_lordo_annuale = db.session.query(func.sum(Reservation.commissioni)).filter(
        Reservation.data_checkin >= inizio_anno,
        Reservation.data_checkin < inizio_anno+timedelta(days=365)
    ).scalar()
    # Se non ci sono prenotazioni, imposta il totale a 0
    totale_lordo_annuale = totale_lordo_annuale or 0 
    
    return totale_lordo_annuale

##CALCOLARE PROFITTO TOTALE ANNO IN CORSO
def calcola_totale_profitto_anno_in_corso():
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
    totale_tax_annuale = db.session.query(func.sum(Reservation.no_tax)).filter(
        Reservation.data_checkin >= inizio_anno,
        Reservation.data_checkin < inizio_anno+timedelta(days=365)
    ).scalar()
    totale_commissioni_annuale = db.session.query(func.sum(Reservation.commissioni)).filter(
        Reservation.data_checkin >= inizio_anno,
        Reservation.data_checkin < inizio_anno+timedelta(days=365)
    ).scalar()
    profitto = totale_lordo_annuale+totale_tax_annuale-totale_commissioni_annuale
    # Se non ci sono prenotazioni, imposta il totale a 0
    profitto = profitto or 0
    
    return profitto

##CALCOLARE PROFITTO TOTALE ANNO PRECEDENTE
def calcola_totale_profitto_anno_precedente():
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
    totale_tax_annuale = db.session.query(func.sum(Reservation.no_tax)).filter(
        Reservation.data_checkin >= inizio_anno,
        Reservation.data_checkin < inizio_anno+timedelta(days=365)
    ).scalar()
    totale_commissioni_annuale = db.session.query(func.sum(Reservation.commissioni)).filter(
        Reservation.data_checkin >= inizio_anno,
        Reservation.data_checkin < inizio_anno+timedelta(days=365)
    ).scalar()
    profitto = totale_lordo_annuale+totale_tax_annuale-totale_commissioni_annuale
    # Se non ci sono prenotazioni, imposta il totale a 0
    profitto = profitto or 0
    
    return profitto

##CALCOLARE TOTALE LORDO ANNO IN CORSO CASA
def calcola_totale_lordo_anno_in_corso_casa(appartamento):
    # Imposta la data di inizio dell'anno (31/10)
    mese_corrente = datetime.today().month
    if mese_corrente >= 1 and mese_corrente <= 10:
        inizio_anno = datetime(datetime.today().year - 1, 10, 31)
    elif  mese_corrente==11 or mese_corrente==12: 
        inizio_anno = datetime(datetime.today().year , 10, 31)

    # Esegue la query per ottenere il totale_lordo delle prenotazioni di quest'anno
    totale_lordo_annuale = db.session.query(func.sum(Reservation.totale_lordo)).filter(
        Reservation.data_checkin >= inizio_anno,
        Reservation.data_checkin < inizio_anno+timedelta(days=365),
        Reservation.immobile == appartamento
    ).scalar()
    # Se non ci sono prenotazioni, imposta il totale a 0
    totale_lordo_annuale = totale_lordo_annuale or 0
    
    return totale_lordo_annuale

def get_financial_data():
    today = datetime.now().date()
    next_six_months = [today + timedelta(days=(30 * i)) for i in range(6)]

    financial_data = defaultdict(lambda: {'entrate': 0, 'uscite': 0})
    
    for month_start in next_six_months:
        month_end = month_start.replace(day=28) + timedelta(days=4)
        monthly_data = (
            db.session.query(
                extract('month', Finance.data_scadenza).label('month'),
                Finance.importo.label('importo')
            )
            .filter(
                Finance.data_scadenza.between(month_start, month_end),
                Finance.importo != 0,
                Finance.stato != 'pagato',
            )
            .all()
        )

        for data in monthly_data:
            if data.importo > 0:
                financial_data[month_start.strftime('%B %Y')]['entrate'] += data.importo
            elif data.importo < 0:
                financial_data[month_start.strftime('%B %Y')]['uscite'] += abs(data.importo)

    return [{'month': month, **data} for month, data in financial_data.items()]
##-------------- FINE FUNZIONI  -----------------

##-------------- INIZIO ROUTE -----------------
#finanze
@app.route('/finanze')
def finanze():
    finance = Finance.query.all()
    finance = get_reservations_sorted_by_scad()
    
    return render_template('Finance.html', finances=finance)

@app.route('/aggiungi_finanza', methods=['POST'])
def aggiungi_finance():
    # Estrai i dati dal modulo
    data_scadenza_str = request.form.get('data_scadenza')
    data_scadenza = datetime.strptime(data_scadenza_str, '%Y-%m-%d').date()
    immobile = request.form.get('immobile')
    portale = request.form.get('portale')
    soggetto = request.form.get('soggetto')
    descrizione = request.form.get('descrizione')
    importo_str = request.form.get('importo', default='0')
    importo = float(importo_str) if importo_str else 0.00
    data_pagamento_str = request.form.get('data_pagamento')
    data_pagamento = datetime.strptime(data_pagamento_str, '%Y-%m-%d').date()
    conto = request.form.get('conto')
    stato = request.form.get('stato')
    # Crea una nuova voce finanziaria
    nuova_finance = Finance(
        data_scadenza=data_scadenza,
        immobile=immobile,
        portale=portale,
        soggetto=soggetto,
        descrizione=descrizione,
        importo=importo,
        data_pagamento=data_pagamento,
        conto=conto,
        stato=stato
    )

    # Aggiungi la nuova voce finanziaria al database
    db.session.add(nuova_finance)
    db.session.commit()
    db.session.close()

    # Redirect alla pagina finanziaria dopo l'inserimento
    return redirect(url_for('finanze'))

@app.route('/modifica_finanza/<int:id>', methods=['GET'])
def modifica_finance(id):
    finance_entry = Finance.query.get(id)
    return render_template('modifica_finance.html', finance_entry=finance_entry)

@app.route('/elimina_finanza/<int:id>', methods=['POST', 'DELETE'])
def elimina_finance(id):
    if request.method in ['POST', 'DELETE']:
        try:
            finance_entry = Finance.query.get(id)
            db.session.delete(finance_entry)
            db.session.commit()
        except Exception as e:
            print(str(e))
            flash('Errore durante l\'eliminazione della voce finanziaria.', 'danger')
    return redirect(url_for('finanze'))

@app.route('/salva_modifiche_finanza/<int:id>', methods=['POST'])
def salva_modifiche_finance(id):
    if request.method == 'POST':
        try:
            finance_entry = Finance.query.get(id)
            # Aggiorna i campi della voce finanziaria in base ai dati del modulo
            finance_entry.data_scadenza = datetime.strptime(request.form['data_scadenza'], '%Y-%m-%d').date()
            finance_entry.soggetto = request.form['soggetto']
            finance_entry.descrizione = request.form['descrizione']
            finance_entry.importo = float(request.form['importo'])
            finance_entry.data_pagamento = datetime.strptime(request.form['data_pagamento'], '%Y-%m-%d').date()
            finance_entry.conto = request.form['conto']
            finance_entry.stato = request.form['stato']
            db.session.commit()
            flash('Modifiche salvate con successo.', 'success')
        except Exception as e:
            print(str(e))
            flash('Errore durante il salvataggio delle modifiche.', 'danger')
    return redirect(url_for('finanze'))

#prenotazioni
@app.route('/')
def Prenotazioni():
    reservations = Reservation.query.all()
    reservations = get_reservations_sorted_by_checkin()
    return render_template('Prenotazioni.html', reservations=reservations)

@app.route('/aggiungi_prenotazione', methods=['POST'])
def aggiungi_prenotazione():
    # Estrai i dati dal form
    data_prenotazione_str = request.form.get('data_prenotazione')
    data_prenotazione = datetime.strptime(data_prenotazione_str, '%Y-%m-%d').date()
    immobile = request.form.get('immobile')
    portale = request.form.get('portale')
    numero = request.form.get('numero', default='0')
    nome_cognome = request.form.get('nome_cognome')
    numero_telefono = request.form.get('numero_telefono', default='0')
    data_checkin_str = request.form.get('data_checkin')
    data_checkin = datetime.strptime(data_checkin_str, '%Y-%m-%d').date()
    data_checkout_str = request.form.get('data_checkout')
    data_checkout = datetime.strptime(data_checkout_str, '%Y-%m-%d').date()
    numero_ospiti_str = request.form.get('numero_ospiti', default='0')
    numero_ospiti = int(numero_ospiti_str) if numero_ospiti_str else 0
    totale_lordo_str = request.form.get('totale_lordo', default='0')
    totale_lordo = float(totale_lordo_str) if totale_lordo_str else 0.00
    no_tax_str = request.form.get('no_tax', default='0')
    no_tax = float(no_tax_str) if no_tax_str else 0.00
    commissioni_str = request.form.get('commissioni', default='0')
    commissioni = float(commissioni_str) if commissioni_str else 0.00
    # Crea una nuova prenotazione
    nuova_prenotazione = Reservation(
                                        data_prenotazione=data_prenotazione,
                                        immobile=immobile,
                                        portale=portale,
                                        numero=numero,
                                        nome_cognome=nome_cognome,
                                        numero_telefono=numero_telefono,
                                        data_checkin=data_checkin,
                                        data_checkout=data_checkout,
                                        numero_ospiti=numero_ospiti,
                                        totale_lordo=totale_lordo,
                                        no_tax=no_tax,
                                        commissioni=commissioni
                                    )

    # Aggiungi la nuova prenotazione al database
    db.session.add(nuova_prenotazione)
    nuova_voce_finanziaria = Finance(
        data_scadenza=nuova_prenotazione.data_checkout,
        immobile=nuova_prenotazione.immobile,
        portale=nuova_prenotazione.portale,
        soggetto=nuova_prenotazione.nome_cognome,
        descrizione = nuova_prenotazione.id if nuova_prenotazione.id is not None else 'valore_predefinito',
        importo=nuova_prenotazione.totale_lordo + nuova_prenotazione.no_tax,
        data_pagamento=nuova_prenotazione.data_checkout,
        conto="ING",
        stato="Da pagare"
    )
    db.session.add(nuova_voce_finanziaria)
    # Commit delle modifiche al database
    db.session.commit()
    id_prenotazione = nuova_prenotazione.id
    nuova_voce_finanziaria.descrizione = str(id_prenotazione)
    db.session.add(nuova_voce_finanziaria)

    nuova_voce_finanziaria = Finance(
        data_scadenza=nuova_prenotazione.data_checkout,
        immobile=nuova_prenotazione.immobile,
        portale=nuova_prenotazione.portale,
        soggetto=nuova_prenotazione.portale,
        descrizione = nuova_prenotazione.id if nuova_prenotazione.id is not None else 'valore_predefinito',
        importo=-1*nuova_prenotazione.commissioni,
        data_pagamento=nuova_prenotazione.data_checkout,
        conto="ING",
        stato="Da pagare"
    )
    db.session.add(nuova_voce_finanziaria)
    db.session.add(nuova_voce_finanziaria)
    # Commit delle modifiche al database
    db.session.commit()
    id_prenotazione = nuova_prenotazione.id
    nuova_voce_finanziaria.descrizione = str(id_prenotazione)
    db.session.add(nuova_voce_finanziaria)

    db.session.close()

    # Redirect alla pagina principale dopo l'inserimento
    return redirect(url_for('Prenotazioni'))

@app.route('/modifica_prenotazione/<int:id>', methods=['GET'])
def modifica_prenotazione(id):
    prenotazione = Reservation.query.get(id)
    return render_template('modifica_prenotazione.html', prenotazione=prenotazione)

@app.route('/elimina_prenotazione/<int:id>', methods=['POST', 'DELETE'])
def elimina_prenotazione(id):
    if request.method in ['POST', 'DELETE']:
        try:
            prenotazione = Reservation.query.get(id)
            
            # Cerca e elimina la riga corrispondente nella tabella Finance
            voce_finanziaria = Finance.query.filter_by(descrizione=prenotazione.id).first()
            if voce_finanziaria:
                db.session.delete(voce_finanziaria)

            # Elimina la prenotazione
            db.session.delete(prenotazione)
            
            # Esegui il commit delle modifiche al database
            db.session.commit()
            
            flash('Prenotazione eliminata con successo.', 'success')
        except Exception as e:
            print(str(e))
            flash('Errore durante l\'eliminazione della prenotazione.', 'danger')

    return redirect(url_for('Prenotazioni'))

@app.route('/salva_modifiche/<int:id>', methods=['POST'])
def salva_modifiche(id):
    if request.method == 'POST':
        try:
            prenotazione = Reservation.query.get(id)
            # Aggiorna i campi della prenotazione in base ai dati del modulo
            prenotazione.nome_cognome = request.form['nome_cognome']
            prenotazione.numero_telefono = request.form['numero_telefono']
            prenotazione.data_checkin = datetime.strptime(request.form['data_checkin'], '%Y-%m-%d').date()
            prenotazione.data_checkout = datetime.strptime(request.form['data_checkout'], '%Y-%m-%d').date()
            prenotazione.numero_ospiti = int(request.form['numero_ospiti'])
            prenotazione.totale_lordo = float(request.form['totale_lordo'])
            prenotazione.no_tax = float(request.form['no_tax'])
            prenotazione.commissioni = float(request.form['commissioni'])
            db.session.commit()

            voce_finanziaria = Finance.query.filter_by(descrizione=prenotazione.id).first()
            if voce_finanziaria:
                voce_finanziaria.data_scadenza = prenotazione.data_checkout
                voce_finanziaria.immobile = prenotazione.immobile
                voce_finanziaria.portale = prenotazione.portale
                voce_finanziaria.soggetto = prenotazione.nome_cognome
                voce_finanziaria.descrizione = str(prenotazione.id)
                voce_finanziaria.importo = prenotazione.totale_lordo + prenotazione.no_tax
                voce_finanziaria.data_pagamento = prenotazione.data_checkout
                voce_finanziaria.conto = "ING"
                voce_finanziaria.stato = "Da pagare"
                db.session.commit()
                flash('Modifiche salvate con successo.', 'success')
            else:
                flash('Voce finanziaria non trovata.', 'danger')

        except Exception as e:
            print(str(e))
            flash('Errore durante il salvataggio delle modifiche.', 'danger')

    return redirect(url_for('Prenotazioni'))#calendario

@app.route('/Calendario')
def Calendario():
    reservations1 = Reservation.query.all()
    reservations_dict_list = [reservation.as_dict() for reservation in reservations1]
    return render_template('Calendario.html', prenotazioni=reservations_dict_list)

##home
def get_total_bookings_for_year(year):
    start_date = datetime(year, 10, 31)  # Data di inizio dell'anno fiscale
    end_date = start_date + timedelta(days=365)  # Data di fine dell'anno fiscale

    total_bookings = Reservation.query.filter(
        Reservation.data_checkin.between(start_date, end_date)
    ).count()

    return total_bookings
@app.route('/home', methods=['GET', 'POST'])
def home():
    years = [str(year) for year in range(2022, 2030)]  # Aggiungi anni secondo necessità

    if request.method == 'POST':
        selected_year = request.form.get('yearSelect')
        total_bookings = get_total_bookings_for_year(int(selected_year))

        return render_template('home.html', years=years, selected_year=selected_year, total_bookings=total_bookings)

    return render_template('home.html', years=years)

#Dashboard
@app.route('/Dashboard')
def Dashboard():
    totale_lordo_annuale_incorso                = calcola_totale_lordo_anno_in_corso()
    totale_lordo_annuale_precedente             = calcola_totale_lordo_anno_precedente()
    variazione_totale_lordo                     = round(((totale_lordo_annuale_incorso-totale_lordo_annuale_precedente)/totale_lordo_annuale_precedente)*100, 2)
    calcola_totale_lordo_anno_in_corso_LaThuile = calcola_totale_lordo_anno_in_corso_casa('LaThuile')
    calcola_totale_lordo_anno_in_corso_Santa    = calcola_totale_lordo_anno_in_corso_casa('Santa')
    percentage_santa                            = round((100*calcola_totale_lordo_anno_in_corso_Santa)/totale_lordo_annuale_incorso, 2)
    percentage_lathuile                         = round((100*calcola_totale_lordo_anno_in_corso_LaThuile)/totale_lordo_annuale_incorso, 2)
    today                                       = datetime.today().date()
    upcoming_reservations                       = Reservation.query.filter(Reservation.data_checkin >= today).order_by(Reservation.data_checkin).limit(5).all()
    calcola_totale_giorni_anno_in_corso1        = calcola_totale_giorni_anno_in_corso()
    calcola_totale_giorni_anno_precedente1      = calcola_totale_giorni_anno_precedente()
    variazione_totale_giorni                    = round(((calcola_totale_giorni_anno_in_corso1-calcola_totale_giorni_anno_precedente1)/calcola_totale_giorni_anno_precedente1)*100, 2)
    calcola_totale_commissioni_anno_in_corso1   = calcola_totale_commissioni_anno_in_corso()
    calcola_totale_commissioni_anno_precedente1 = calcola_totale_commissioni_anno_precedente()
    variazione_totale_commissioni               = round(((calcola_totale_commissioni_anno_in_corso1-calcola_totale_commissioni_anno_precedente1)/calcola_totale_commissioni_anno_precedente1)*100, 2)
    calcola_totale_profitto_anno_in_corso1      = calcola_totale_profitto_anno_in_corso()
    calcola_totale_profitto_anno_precedente1    = calcola_totale_profitto_anno_precedente()
    proditto_medio_per_notte_anno_in_corso      = round(calcola_totale_profitto_anno_in_corso1/calcola_totale_giorni_anno_in_corso1,2)
    proditto_medio_per_notte_anno_precedente    = round(calcola_totale_profitto_anno_precedente1/calcola_totale_giorni_anno_precedente1,2)
    variazione_totale_prezzo_medio              = round(((proditto_medio_per_notte_anno_in_corso-proditto_medio_per_notte_anno_precedente)/proditto_medio_per_notte_anno_precedente)*100, 2)
    get_check_ins_in_next_7_days1               = get_check_ins_in_next_7_days()
    return render_template('Dashboard.html',    totale_lordo_annuale_incorso=totale_lordo_annuale_incorso, 
                                                totale_lordo_annuale_precedente=totale_lordo_annuale_precedente,
                                                variazione_totale_lordo=variazione_totale_lordo,
                                                calcola_totale_lordo_anno_in_corso_LaThuile=calcola_totale_lordo_anno_in_corso_LaThuile,
                                                calcola_totale_lordo_anno_in_corso_Santa=calcola_totale_lordo_anno_in_corso_Santa,
                                                percentage_lathuile=percentage_lathuile,
                                                percentage_santa=percentage_santa,
                                                reservations=upcoming_reservations,
                                                calcola_totale_giorni_anno_in_corso=calcola_totale_giorni_anno_in_corso1,
                                                calcola_totale_giorni_anno_precedente=calcola_totale_giorni_anno_precedente1,
                                                variazione_totale_giorni=variazione_totale_giorni,
                                                calcola_totale_commissioni_anno_in_corso = calcola_totale_commissioni_anno_in_corso1,
                                                calcola_totale_commissioni_anno_precedente = calcola_totale_commissioni_anno_precedente1,
                                                variazione_totale_commissioni=variazione_totale_commissioni,
                                                proditto_medio_per_notte_anno_in_corso=proditto_medio_per_notte_anno_in_corso,
                                                proditto_medio_per_notte_anno_precedente=proditto_medio_per_notte_anno_precedente,
                                                variazione_totale_prezzo_medio=variazione_totale_prezzo_medio,
                                                get_check_ins_in_next_7_days=get_check_ins_in_next_7_days1
                                                )

@app.route('/grap', methods=['GET'])
def grap():
    financial_data = get_financial_data()
    print(financial_data)
    return jsonify(financial_data)

@app.route('/api/incassi', methods=['GET'])
def get_incassi():
    dataInput1 = request.args.get('dataInput1')
    dataInput2 = request.args.get('dataInput2')
    immobileInput = request.args.get('immobileInput')

    # Logica per ottenere gli incassi in base ai criteri specificati
    if immobileInput == 'Tutti':
        incassi = Reservation.query.filter(
            Reservation.data_checkin >= dataInput1,
            Reservation.data_checkout <= dataInput2
        ).all()
    else:
        incassi = Reservation.query.filter(
            Reservation.data_checkin >= dataInput1,
            Reservation.data_checkout <= dataInput2,
            Reservation.immobile == immobileInput
        ).all()

    # Calcola il totale degli incassi
    totale_incassi = sum(incasso.totale_lordo for incasso in incassi)

    return jsonify({'totale_incassi': totale_incassi})



if __name__ == '__main__':
    if 'liveconsole' not in gethostname():
        app.run()

