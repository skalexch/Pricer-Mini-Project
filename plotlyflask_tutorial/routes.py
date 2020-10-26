"""Routes for parent Flask app."""
from flask import render_template
from flask import current_app as app
from flask import request, redirect, url_for
import pandas as pd
import numpy as np
import flask
import math
import os
from werkzeug.utils import secure_filename
from scipy.optimize import root
from datetime import datetime


@app.route('/')
def home():
    """Landing page."""
    return render_template(
        'index.jinja2',
        title='Plotly Dash Flask Tutorial',
        description='Embed Plotly Dash into your Flask applications.',
        template='home-template',
        body="This is a homepage served with Flask."
    )


UPLOAD_FOLDER = 'data'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/', methods=['POST'])
def upload_file():
    uploaded_file = request.files['file']
    if uploaded_file.filename != '':
        uploaded_file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'pred.csv'))
        filename = secure_filename(uploaded_file.filename)
        
        maturity = int(request.form['maturity'])
        freq = request.form['freq']
        type_taux = request.form['type_taux']
        dealtype = request.form['dealtype']
        #marge = request.form['marge']
        l={'params':[maturity,freq,type_taux,dealtype]}
        fwd_params=pd.DataFrame(data=l)
        fwd_params.to_csv("data/fwd_params.csv")
        
    return redirect(url_for('home',))




###################Pricers and optimizers
from math import*
def f(deal,maturity,amount,time_type,frequency,spot,interest_rate_first_currency,interest_rate_second_currency,commercial_margin):
  cf=0
  def g(a):
    x=1
    if a=='Trimestriel':
          x=90
    elif a=='Semestriel':
          x=180
    elif a=='Annuel':
          x=360
    return x
  if deal=='Achat':
      sig=1
  else:
      sig=-1
  if time_type=='Discret':
    if maturity<=g(frequency):
      cf=spot*(1+float(interest_rate_first_currency)*0.01*maturity/g(frequency))/(1+float(interest_rate_second_currency)*0.01*maturity/g(frequency))+commercial_margin*0.0001*sig
    else:
      cf=spot*((1+(float(interest_rate_first_currency)/(360/g(frequency)))*0.01)**maturity/g(frequency))/((1+float(interest_rate_second_currency)*0.01)**maturity/g(frequency))+sig*commercial_margin*0.0001
  else:
    cf=(spot*exp(float(interest_rate_first_currency)*0.01*maturity/g(frequency))/exp(float(interest_rate_second_currency)*0.01*maturity/g(frequency)))+commercial_margin*0.0001*sig
  return cf


def spot_from_forward(deal,maturity,amount,time_type,frequency,fwd,interest_rate_first_currency,interest_rate_second_currency,commercial_margin):
  cf=0
  def g(a):
    x=1
    if a=='Trimestriel':
          x=90
    elif a=='Semestriel':
          x=180
    elif a=='Annuel':
          x=360
    return x

  if deal=='Achat':
      sig=-1
  else:
      sig=1
      
  if time_type=='Discret':
    if maturity<=g(frequency):
      cf=fwd/(1+float(interest_rate_first_currency)*0.01*maturity/g(frequency))*(1+float(interest_rate_second_currency)*0.01*maturity/g(frequency))+sig*commercial_margin*0.0001
    else:
      cf=fwd/((1+(float(interest_rate_first_currency)/(360/g(frequency)))*0.01)**maturity/g(frequency))*((1+float(interest_rate_second_currency)*0.01)**maturity/g(frequency))+sig*commercial_margin*0.0001
  else:
    cf=(fwd*exp((-1)*float(interest_rate_first_currency)*0.01*maturity/g(frequency))/exp(float(interest_rate_second_currency)*0.01*maturity/g(frequency)))+sig*commercial_margin*0.0001
  return round(cf,4)


def local_rate_from_forward(deal,maturity,amount,time_type,frequency,fwd,spot,interest_rate_second_currency,commercial_margin):
  cf=0
  def g(a):
    x=1
    if a=='Trimestriel':
          x=90
    elif a=='Semestriel':
          x=180
    elif a=='Annuel':
          x=360
    return x

  if deal=='Achat':
      sig=1
  else:
      sig=-1
      
  if time_type=='Discret':
    if maturity<=g(frequency):
      cf=(((fwd-sig*commercial_margin*0.0001)/spot)*(1+float(interest_rate_second_currency)*0.01*maturity/g(frequency))-1)/(maturity/g(frequency))
    else:
      cf=(((fwd-sig*commercial_margin*0.0001)/spot)**(g(frequency)/maturity)*(1+float(interest_rate_second_currency)*0.01*maturity/g(frequency))-1)/(maturity/g(frequency))
  else:
    cf=((math.log((fwd-sig*commercial_margin*0.0001)/spot)*(1+float(interest_rate_second_currency)*0.01*maturity/g(frequency)))-1)/(maturity/g(frequency))
  return round(cf*100,4)



def foreign_rate_from_forward(deal,maturity,amount,time_type,frequency,fwd,spot,interest_rate_first_currency,commercial_margin):
  cf=0
  def g(a):
    x=1
    if a=='Trimestriel':
          x=90
    elif a=='Semestriel':
          x=180
    elif a=='Annuel':
          x=360
    return x

  if deal=='Achat':
      sig=1
  else:
      sig=-1
      
  if time_type=='Discret':
    if maturity<=g(frequency):
      cf=((((fwd-sig*commercial_margin*0.0001)/spot)**(-1))*(1+float(interest_rate_first_currency)*0.01*maturity/g(frequency))-1)/(maturity/g(frequency))
    else:
      cf=((((fwd-sig*commercial_margin*0.0001)/spot)**(g(frequency)/maturity)**(-1))*(1+float(interest_rate_first_currency)*0.01*maturity/g(frequency))-1)/(maturity/g(frequency))
  else:
    cf=((math.log(((fwd-sig*commercial_margin*0.0001)/spot)**(-1))*(1+float(interest_rate_first_currency)*0.01*maturity/g(frequency)))-1)/(maturity/g(frequency))
  return round(cf*100,4)




###################################

@app.route('/calc/', methods=['POST','GET'])
def calculate():
    if flask.request.method == 'GET':
        return(flask.render_template('forms1.html'))
    if flask.request.method == 'POST':
      if 'Do Something' in flask.request.form.values():
        L=['Maturité_en_jours','Montant','Continu_ou_Discret',"Frequence_du_taux_d'interet",'Cours_Spot',"Taux_d'interet_local","Taux_d'interet_etranger",'Marge_Commerciale','clt_rate','deal','fwd','opt']
        cf=''
        clt_rate=0
        Maturité_en_jours=float(flask.request.form[L[0]])
        Montant=float(flask.request.form[L[1]])
        Continu_ou_Discret=flask.request.form[L[2]]
        Frequence_du_taux_dinteret=flask.request.form[L[3]]
        Cours_Spot=float(flask.request.form[L[4]])
        trloc=float(flask.request.form[L[5]])
        tretr=float(flask.request.form[L[6]])
        marge=float(flask.request.form[L[7]])
        
        clt_rate=flask.request.form[L[8]]
        if clt_rate!='':
            clt_rate=float(clt_rate)
        else:
            clt_rate=0
            
        deal=flask.request.form[L[9]]

        cf=flask.request.form[L[10]]
        opt=flask.request.form[L[11]]

        if cf!='':
            cf=float(cf)
        else:
            cf=0

            
        if opt=='Forward':
            cf=f(deal,Maturité_en_jours,Montant,Continu_ou_Discret,Frequence_du_taux_dinteret,Cours_Spot,trloc,tretr,marge)
        elif opt=='Spot':
            Cours_Spot=spot_from_forward(deal,Maturité_en_jours,Montant,Continu_ou_Discret,Frequence_du_taux_dinteret,clt_rate,trloc,tretr,marge)
            cf=f(deal,Maturité_en_jours,Montant,Continu_ou_Discret,Frequence_du_taux_dinteret,Cours_Spot,trloc,tretr,marge)

        elif opt=="Taux d'interet local":
            trloc=local_rate_from_forward(deal,Maturité_en_jours,Montant,Continu_ou_Discret,Frequence_du_taux_dinteret,clt_rate,Cours_Spot,tretr,marge)
            cf=f(deal,Maturité_en_jours,Montant,Continu_ou_Discret,Frequence_du_taux_dinteret,Cours_Spot,trloc,tretr,marge)



        #cf = f(Maturité_en_jours,Montant,Continu_ou_Discret,Frequence_du_taux_dinteret,Cours_Spot,trloc,tretr,marge)
        mar=(cf-marge*0.0001-clt_rate)*10000
        fwd_am=Montant*cf
        if clt_rate==0 or clt_rate=="":
            mar=""
        elif deal=="Achat":
            if mar>0:
                mar="Marge réalisée en pips="+str(abs(math.floor(mar)))       
            else:
                mar="Marge négative"
        elif deal=="Vente":
            if mar>2:
                mar="Marge négative"
            else:
                mar="Marge réalisée en pips="+str(abs(math.floor(mar)))            
            

        return flask.render_template('forms2.html', result=round(cf,4), fwd_amount=round(fwd_am,2), margin=mar, mat=Maturité_en_jours,mtt=Montant,spot=Cours_Spot,trl=trloc,tret=tretr,mar=marge, clr=clt_rate)






@app.route('/swap/', methods=['POST','GET'])
def calc_swap():
    if flask.request.method == 'GET':
        return(flask.render_template('swap_form.html'))
    if flask.request.method == 'POST':
      if 'Do Something' in flask.request.form.values():
        L=['Maturité_en_jours','Montant','Continu_ou_Discret',"Frequence_du_taux_d'interet",'Cours_Spot',"Taux_d'interet_local","Taux_d'interet_etranger",'deal','Maturité_en_jours2']

        Maturité_en_jours=float(flask.request.form[L[0]])
        Maturité_en_jours2=float(flask.request.form[L[8]])
        Montant=float(flask.request.form[L[1]])
        Continu_ou_Discret=flask.request.form[L[2]]
        Frequence_du_taux_dinteret=flask.request.form[L[3]]
        Cours_Spot=float(flask.request.form[L[4]])
        trloc=float(flask.request.form[L[5]])
        tretr=float(flask.request.form[L[6]])
        deal=flask.request.form[L[7]]

        cf1= f(deal,Maturité_en_jours,Montant,Continu_ou_Discret,Frequence_du_taux_dinteret,Cours_Spot,trloc,tretr,0)
        cf2= f(deal,Maturité_en_jours2,Montant,Continu_ou_Discret,Frequence_du_taux_dinteret,Cours_Spot,trloc,tretr,0)
        #mazelet formule swap w les cas           
        if Maturité_en_jours==0: #cas spot forward
            cf1=Cours_Spot
            pts_swap=(cf2-cf1)*10000
        else: #cas 2 forwards
            pts_swap=(cf2-cf1)*10000


        return flask.render_template('swap_form2.html', result=round(cf1,4), result2=round(cf2,4), swap=abs(math.floor(pts_swap)), mat=Maturité_en_jours, mat2=Maturité_en_jours2,mtt=Montant,spot=Cours_Spot,trl=trloc,tret=tretr)

######################SWAP OPTIMIZER###############
#####Predefined functions


def create_dataframe_for_opt(path):
    """Create Pandas DataFrame from local CSV."""
    df = pd.read_csv(path)
    df=df.set_index(df['Date'])
    df.index=pd.to_datetime(df.index,format='%b %d, %Y')
    df=df.drop('Date',axis=1)
    
    df['interest_rate_first_currency_bid']=7
    df['interest_rate_first_currency_ask']=7

    df['interest_rate_second_currency_bid']=3
    df['interest_rate_second_currency_ask']=3
    df['Price_bid']=df['Dernier']
    df['Price_ask']=df['Plus Haut']
    df=df[['Price_bid','Price_ask','interest_rate_first_currency_bid','interest_rate_first_currency_ask','interest_rate_second_currency_bid','interest_rate_second_currency_ask']]
    starting=0
    df=df[starting:]#starting from 2019
    return df



#########################

##@app.route('/', methods=['POST'])
##def upload_file2():
##    uploaded_file = request.files['file2']
##    if uploaded_file.filename != '':
##        uploaded_file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'client_data.csv'))
##        filename = secure_filename(uploaded_file.filename)
##    
##    return redirect(url_for('home',))
##
##
##@app.route('/swap_optimizer/', methods=['POST','GET'])
##def swap_optimizer():
##    if flask.request.method == 'GET':
##        return(flask.render_template('swap_opt.html'))
##    if flask.request.method == "POST":
##        uploaded_file = request.files['data_files']
##        if uploaded_file.filename != '':
##            uploaded_file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'client_data.csv'))
##            filename = secure_filename(uploaded_file.filename)
##        return redirect(url_for('swap_optimizer'))
##
##    
##        client_data=pd.read_csv("data/client_data.csv")
##        eurtnd=pd.read_csv("data/cours/eutn.csv")
##        usdtnd=pd.read_csv("data/cours/ustn.csv")
##        chftnd=pd.read_csv("data/cours/chtn.csv")
##
##
##        #Here we apply optimize
##
##        return flask.render_template('swap_opt2.html',l=client_data)
##


#######################################################
#######################################################
########################################################
################Bonds#################


def bond_price(face_value,nominal_rate,mat,freq,infine,r):


    if freq==2:
        nominal_rate=nominal_rate/2
        r=r/2
        mat=mat*2
    elif freq==4:
        nominal_rate=nominal_rate/4
        r=r/4
        mat=mat*4
        
    coupon_flow=nominal_rate*face_value/100
    r=r/100
    price=0
    for i in range(1,mat+1):
        price+=coupon_flow/((1+r)**i)
    price+=face_value/((1+r)**mat)
    return price

def bond_duration(face_value,nominal_rate,mat,freq,infine,r,prix):

    if freq==2:
        nominal_rate=nominal_rate/2
        r=r/2
        mat=mat*2
    elif freq==4:
        nominal_rate=nominal_rate/4
        r=r/4
        mat=mat*4


    coupon_flow=nominal_rate*face_value/100
    r=r/100
    duration=0
    for i in range(1,mat+1):
        duration+=(i*coupon_flow)/(1+r)**i
    duration+=(mat*face_value)/(1+r)**mat
    duration=duration/prix/freq
    return duration

def bond_yield(face_value,nominal_rate,mat,freq,infine,prix):

    x1=nominal_rate
    y1=face_value
    
    x2=x1+1
    y2=bond_price(face_value,nominal_rate,mat,freq,infine,x2)
    if face_value>prix:
        while y2>prix:
            x2=x1+1
            y2=bond_price(face_value,nominal_rate,mat,freq,infine,x2)            
    elif face_value<prix:
        while y2<prix:
            x2=x1-1
            y2=bond_price(face_value,nominal_rate,mat,freq,infine,x2)            
    
    x=x1+(prix-y1)*(x2-x1)/(y2-y1)
    
    return x

@app.route('/bond/', methods=['POST','GET'])
def bonds():
    if flask.request.method == 'GET':
        return(flask.render_template('bond_form.html'))
    if flask.request.method == 'POST':
      if 'Do Something' in flask.request.form.values():
        FV=float(flask.request.form['FV'])
        coupon_rate=float(flask.request.form['coupon_rate'])
        mat_date=flask.request.form['maturity']
        maturity = datetime.strptime(request.form['maturity'], '%Y-%m-%d')
        em_date=flask.request.form['emission']
        emission = datetime.strptime(request.form['emission'], '%Y-%m-%d')
        frequency=flask.request.form['frequency']
        in_fine='YES'
        price=float(flask.request.form['price'])
        rate=float(flask.request.form['rate'])
        opt=flask.request.form['opt']
        
        if frequency=="Annuel":
            freq=1
        elif frequency=="Semestriel":
            freq=2
        elif frequency=="Trimestriel":
            freq=4

        if maturity.day==emission.day and maturity.month==emission.month:
            mat=int((maturity-emission).days/365)
            cc_days=0
        else:
            mat=int((maturity-emission).days/365)+1
            cc_days=mat*365-(maturity-emission).days

            
        if opt=='Prix':
            price=bond_price(FV,coupon_rate,mat,freq,in_fine,rate)
        elif opt=='Taux de rendement':
            rate=bond_yield(FV,coupon_rate,mat,freq,in_fine,price)

        duration=bond_duration(FV,coupon_rate,mat,freq,in_fine,rate,price)
        
        cc=FV*coupon_rate*cc_days/360/100
        clean=price-cc

        return flask.render_template('bond_form2.html', rate=round(rate,2),duration=round(duration,2), clean=round(clean,2), cc=round(cc,2),price=round(price,2), coupon_rate=coupon_rate, FV=FV,mat_date=mat_date,em_date=em_date)







