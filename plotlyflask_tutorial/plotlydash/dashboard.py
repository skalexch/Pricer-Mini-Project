"""Instantiate a Dash app."""
import numpy as np
import pandas as pd
import dash
import dash_table
import dash_html_components as html
import dash_core_components as dcc
from .layout import html_layout
#from .data import create_dataframe
import plotly.graph_objects as go

def create_dataframe(path):
    """Create Pandas DataFrame from local CSV."""
    df = pd.read_csv(path)
    df=df.set_index(df['Date'])
    df.index=pd.to_datetime(df.index,format='%b %d, %Y')
    df=df.drop('Date',axis=1)
    df['interest_rate_first_currency']=7
    df['interest_rate_second_currency']=3
    df=df[['Price','interest_rate_first_currency','interest_rate_second_currency']]
    starting=0
    df=df[starting:]#starting from 2019
    return df


from math import*
def f(maturity,amount,time_type,frequency,spot,interest_rate_first_currency,interest_rate_second_currency,commercial_margin):
  cf=0
  def g(a):
    x=1
    if a=='Trimestrial':
          x=90
    elif a=='Semestrial':
          x=180
    elif a=='Annual':
          x=360
    return x   
  if time_type=='Discrete':
    if maturity<=360:
      cf=spot*(1+float(interest_rate_second_currency)*0.01*maturity/g(frequency))/(1+float(interest_rate_first_currency)*0.01*maturity/g(frequency))+commercial_margin*0.0001
    else:
      cf=spot*((1+float(interest_rate_second_currency)*0.01)**maturity/g(frequency))/((1+float(interest_rate_first_currency)*0.01)**maturity/g(frequency))+commercial_margin*0.0001
  else:
    cf=(spot*exp(float(interest_rate_second_currency)*0.01*maturity/g(frequency))/exp(float(interest_rate_first_currency)*0.01*maturity/g(frequency)))+commercial_margin*0.0001
  return cf


def backtest(df,maturity,time_type,frequency,amount,commercial_margin,f):
  df['Forward']=0.0
  for i in range(df.shape[0]-maturity):
    df['Forward'].iloc[i+maturity]=f(maturity,amount,time_type,frequency,df['Price'].iloc[i],df['interest_rate_second_currency'].iloc[i],df['interest_rate_first_currency'].iloc[i],commercial_margin)
  return df



def plott(a,client_type,maturity):
  fig = go.Figure()
  l=a['Forward'][maturity:]-a['Price'][maturity:]
  my_stocks=a[maturity:]
  pos=pd.Series(l.index)
  neg=pd.Series(l.index)
  for i in range(len(l)):
    if l.iloc[i]>0:
      pos.iloc[i]=l.iloc[i]
      neg.iloc[i]=0.0
    elif l.iloc[i]<0:
      neg.iloc[i]=l.iloc[i]
      pos.iloc[i]=0.0
  if client_type=='Sell':
    fig.add_trace(go.Scatter(x=l.index,y=pos.values,marker_color='rgb(111, 231, 120)',fill = "tozeroy",fillcolor="rgba(111, 231, 120,0.3)",name='Gain'))
    fig.add_trace(go.Scatter(x=l.index,y=neg.values,marker_color='red',fill = "tozeroy",fillcolor="rgba(255, 0, 0, 0.2)",name='Loss'))
    fig.update_layout(title = 'Gain/Loss',font=dict(size=24),title_x=0.5)
    fig.update_layout(showlegend=True)
    

  elif client_type=='Buy':
    fig.add_trace(go.Scatter(x=l.index,y=pos.values,marker_color='red',fill = "tozeroy",fillcolor="rgba(255, 0, 0, 0.2)",name='Loss'))
    fig.add_trace(go.Scatter(x=l.index,y=neg.values,marker_color='rgb(111, 231, 120)',fill = "tozeroy",fillcolor="rgba(111, 231, 120,0.3)",name='Gain'))
    fig.update_layout(title = 'Gain/Loss',font=dict(size=24),title_x=0.5)
    fig.update_layout(showlegend=True)
  return fig  


def eval(backtest,m,client_type,maturity):
  backtest['month']=backtest.index.month
  backtest['diff']=backtest['Forward'][maturity:]-backtest['Price'][maturity:]
  a=backtest[backtest['month']==m]
  l=a['diff']
  pos=pd.Series(index=l.index)
  neg=pd.Series(index=l.index)
  for i in range(len(l)):
      if l.iloc[i]>0:
        pos.iloc[i]=l.iloc[i]
        neg.iloc[i]=0.0
      elif l.iloc[i]<0:
        neg.iloc[i]=l.iloc[i]
        pos.iloc[i]=0.0
  if client_type=='Sell':
    prc_gain_in_count=round(len(pos[pos>0])*100/len(pos),2)
    value_gained=pos[pos>0].mean()
    value_lost=neg[neg<0].mean()
    max_gain=pos.max()
    max_gain_day=pos.idxmax()
    max_loss=neg.min()
    max_loss_day=pos.idxmin()

  if client_type=='Buy':
    prc_gain_in_count=round(len(neg[neg<0])*100/len(neg),2)
    value_gained=-neg[neg<0].mean()
    value_lost=-pos[pos>0].mean()
    max_gain=neg.min()*-1
    max_gain_day=neg.idxmin()
    max_loss=pos.max()*-1
    max_loss_day=pos.idxmax()
    
  return prc_gain_in_count,round(value_gained,4),round(value_lost,4),round(max_gain,4),max_gain_day,round(max_loss,4),max_loss_day






########################################################




def init_dashboard(server):
    """Create a Plotly Dash dashboard."""
    dash_app = dash.Dash(
        server=server,
        routes_pathname_prefix='/dashapp/',
        external_stylesheets=[
            '/static/dist/css/styles.css',
            'https://fonts.googleapis.com/css?family=Lato'
        ]
    )

    # Load DataFrame

    

    # Custom HTML layout
    dash_app.index_string = html_layout




    
    def serve_layout():
        df = create_dataframe('data/pred.csv')
        params=pd.read_csv("data/fwd_params.csv")
        date=df.index
        maturity=int(params.iloc[0][1])
        frequency=params.iloc[1][1]
        time_type=params.iloc[2][1]
        dealtype=params.iloc[3][1]
        df=backtest(df,maturity,time_type,frequency,0,0,f)

        fig = go.Figure()
        my_stocks=df.iloc[maturity:]
        fig.add_trace(go.Scatter(x=my_stocks.index,y=my_stocks['Price'],name='Actual spot'))
        fig.add_trace(go.Scatter(x=my_stocks.index,y=my_stocks['Forward'],name='Forward'))
        fig.update_layout(title = 'Real VS Predicted Forward Rate',font=dict(size=24),title_x=0.5)


        fig2 = go.Figure()
        difference=df['Forward'][maturity:]-df['Price'][maturity:]
        fig2.add_trace(go.Scatter(x=my_stocks.index,y=difference,name='diff'))
        x = np.arange(df.shape[0])
       # fig2.add_trace(data=go.Scatter(x=x, y=0))
        fig2.update_layout(title = 'Rate Difference',font=dict(size=18))

        
        fig2=plott(df,dealtype,maturity)




        prc=[]
        gain=[]
        loss=[]
        max_gain=[]
        max_gain_day=[]
        max_loss=[]
        max_loss_day=[]
        for i in range(1,13):
          l=eval(df,i,dealtype,maturity)
          prc.append(l[0])
          gain.append(l[1])
          loss.append(l[2])
          max_gain.append(l[3])
          max_gain_day.append(l[4])
          max_loss.append(l[5])
          max_loss_day.append(l[6])

        dd=pd.DataFrame(columns={"percentage gain in days","mean_gained","mean_lost","max_gain","max_gain_on_day","max_loss","max_loss_on_day"})
        dd['Month']=range(1,13)
        dd['value_lost']=[0 for i in range(12)]
        dd['percentage gain in days']=prc
        dd['mean_gained']=gain
        dd['mean_lost']=loss
        dd['max_gain']=max_gain
        dd['max_loss']=max_loss
        cols=["Month","percentage gain in days","mean_gained","mean_lost","max_gain","max_loss"]
        dd=dd[cols]



        #Calculating monthly gains
        gains=[]
        months=[i for i in range(12)]
        for i in range(12):
            m=difference.iloc[30*i:30*(i+1)]
            gains.append(round(m.mean(),6))

        period=[str(i)+" Months" for i in range(2,13)]
        period.insert(0, "1 Month")
        df_diff=pd.DataFrame(period,index=months, columns=["Period"])
        df_diff["efficiency expectation"]=gains


        view_df=df
        view_df["Price"]=view_df["Price"].shift((-1)*maturity)
        
        return html.Div(
            children=[dcc.Graph(
                id='histogram-graph',
                figure=fig),
                dcc.Graph(
                id='graph2',
                figure=fig2),
                create_data_table(dd,'difference-table'),
                create_data_table(df.iloc[maturity:],'database-table')
            ],
            id='dash-container'
        )
    
    dash_app.layout = serve_layout
    return dash_app.server


def create_data_table(df,idname):
    """Create Dash datatable from Pandas DataFrame."""
    table = dash_table.DataTable(
        id=idname,
        columns=[{"name": i, "id": i} for i in df.columns],
        data=df.to_dict('records'),
        css=[{
        'selector': '.dash-spreadsheet td div',
        'rule': '''
            line-height: 15px;
            max-height: 30px; min-height: 30px; height: 30px;
            display: block;
            overflow-y: hidden;
        '''
        }],
        sort_action="native",
        sort_mode='native',
        page_size=50
    )
    return table
