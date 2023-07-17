# Arthur Jeannerot - May 2022

import bql
import pandas as pd
from ipywidgets import VBox, HBox, HTML, Button, DatePicker, Dropdown, Text, Tab, Textarea, Box, Layout, Accordion, Label
from datetime import date, datetime,timedelta
from dateutil.relativedelta import relativedelta
import ipydatagrid as ipdg
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


bq = bql.Service()


app_des = '''
        <div style ="color:ivory; background-color:DimGrey; padding:13px; border-radius: 25px;">
            <span style ="font-weight:bold"> Description: </span><br> 
            Over the past 3 years, aggregate Open Interest in Dividend Futures has increased more than 10-fold. 
            There are now 6 Equity Indices with an active Index Dividend Futures market, while the Euro Stoxx 50 also 
            has a highly liquid single-stock dividend futures market. 
            (<a href="https://www.eurex.com/resource/blob/2687950/5c56f865e2f3625c1c75f90991d4c027/data/factsheet_dividend-derivatives.pdf">Eurex Fact Sheet</a>)
            <br>
            Use BQL and BQuant to analyze Index Dividend Futures over time and, in the case of SX5E, 
            drill down into a single name to compare broker dividend estimates to the dividend futures market.        
            <br>
            <span style="font-weight:bold"> Instructions: </span>
            <ul>
            <li>Select an Equity Index from the list <br></li>
            <li>Select a start and end date using the date pickers <br></li>
            <li>Input currency code in the Currency field<br></li>
            <li>Hit the <span style="font-style:italic; font-weight:bold"><u>Get Data</u></span> button to generate the visualisation <br></li>
            </ul>
            <span style="font-weight:bold"> Submit Your Ideas for the Next Bite: </span>
            <li>bquant3@bloomberg.net<br></li>
        </div>


'''


class DividendApp(VBox):


    def __init__(self, bq_serv = None):
        super().__init__()
        self.bq = bq_serv
        self.widgets = {}
        self._build_view()


##### UI AND UTILITIES FUNCTIONS
        
    def get_model_settings(self):
        '''
        Store model settings to use in other functions
        '''


        index_info = {'CAC 40' : 'XFDA Index', 
                    'Euro Stoxx 50' : 'DEDA Index',
                    'Euro Stoxx 50 Banks' : 'DBEA Index', 
                    'FTSE 100' : 'UKDA Index',
                    'Nikkei 225' : 'MNDA Index', 
                    'S&P 500' : 'ASDA Index'}
        
        
        index_mapping = {'XFDA Index' : 'CAC Index',
                         'DEDA Index' : 'SX5E Index',
                         'DBEA Index' : 'SX7E Index',
                         'UKDA Index' : 'UKX Index',
                         'MNDA Index' : 'NKY Index',
                         'ASDA Index' : 'SPX Index'}


        settings = {'index_info' :  index_info,
                    'index_mapping' : index_mapping}


        return settings
    
    
    def get_idx_members(self):
        '''
        Pull index members from BQL and turn them into a list to be used in user selection dropdown
        '''

        
        univ = bq.univ.members('SX5E Index').filter(bq.data.id() != 'FLTR ID Equity').translatesymbols(targetidtype='FUNDAMENTALTICKER')
        
                
        fields = {'Ticker' : bq.data.id()['value'].groupsort(order='asc'),  # Sort ticker list in alphabetical order
                  'Name' : bq.data.name()['value']}


        req = bql.Request(univ, fields)
        res = bq.execute(req)


        tickers_df = pd.concat([fld.df()[fld.name] for fld in res], axis=1, sort=False)
        tickers_dict = dict(zip(tickers_df['Ticker'], tickers_df['Name']))


        return tickers_dict


    def _build_view(self):
        '''
        Create all widgets necessary to build the UI
        '''

        app_settings = self.get_model_settings()

        # Widgets for Index View
        # Labels
        self.widgets['idx_ticker_label'] = Label(value = 'Index', layout = Layout(width = '100px'))
        self.widgets['idx_start_label'] = Label(value = 'Start Date', layout = Layout(width = '100px'))
        self.widgets['idx_end_label'] = Label(value = 'End Date', layout = Layout(width = '100px'))      
        
        
        # Default dates
        end_date = date.today()
        start_date = end_date - relativedelta(months=3)
        
        # User input widgets
        self.widgets['idx_ticker'] = Dropdown(options = app_settings['index_info'], value = 'DEDA Index', layout = Layout(width = '200px'))
        self.widgets['idx_start_dt'] = DatePicker(value = start_date, layout = Layout(width = '200px'))
        self.widgets['idx_end_dt'] = DatePicker(value = end_date, layout = Layout(width = '200px'))
        self.widgets['index_button'] = Button(description = 'Get Data', button_style = 'Primary')
        self.widgets['index_button'].on_click(self.index_run)
        self.widgets['idx_btn_view'] = HBox([self.widgets['index_button']], layout = {'margin': '20px 0px 20px 0px'})
        self.widgets['idx_oi_chart'] = VBox()
        
        # Complete Index View
        self.widgets['index_view'] = VBox([HBox([self.widgets['idx_ticker_label'], self.widgets['idx_ticker']]),
                                          HBox([self.widgets['idx_start_label'], self.widgets['idx_start_dt']]),
                                          HBox([ self.widgets['idx_end_label'], self.widgets['idx_end_dt']]),
                                          self.widgets['idx_btn_view']])


        # Widgets for Single Stock View
        # Labels
        self.widgets['stock_ticker_label'] = Label(value = 'Ticker', layout = Layout(width = '100px'))
        self.widgets['stock_start_label'] = Label(value = 'Start Date', layout = Layout(width = '100px'))
        self.widgets['stock_end_label'] = Label(value = 'End Date', layout = Layout(width = '100px'))
        self.widgets['stock_currency_label'] = Label(value = 'Currency', layout = Layout(width = '100px'))
        
        
        # User input widgets
        self.widgets['stock_ticker'] = Dropdown(options = list(self.get_idx_members().keys()), layout = Layout(width = '200px'))
        self.widgets['stock_start_dt'] = DatePicker(value=start_date, layout = Layout(width = '200px'))
        self.widgets['stock_end_dt'] = DatePicker(value=end_date, layout = Layout(width = '200px'))
        self.widgets['stock_currency'] = Text(value='EUR', layout = Layout(width = '200px'))
        
        
        self.widgets['stock_btn'] = Button(description = 'Get Data', button_style = 'Primary')
        self.widgets['stock_btn'].on_click(self.stock_run)
        self.widgets['stock_btn_view'] = HBox([self.widgets['stock_btn']], layout = {'margin': '20px 0px 20px 0px'})

        
        # Complete Stock View
        self.widgets['stock_view'] = VBox([HBox([self.widgets['stock_ticker_label'], self.widgets['stock_ticker']]),
                                           HBox([self.widgets['stock_start_label'], self.widgets['stock_start_dt']]),
                                           HBox([self.widgets['stock_end_label'], self.widgets['stock_end_dt']]),
                                           HBox([self.widgets['stock_currency_label'],self.widgets['stock_currency']]),
                                           self.widgets['stock_btn_view']])
        
        # Tabs to contain the 2 views
        tab_children = {'Index Futures' : self.widgets['index_view'],
                        'Single Stock': self.widgets['stock_view']}        
        tabs = Tab(children = [*tab_children.values()])
        for index,title in enumerate(tab_children.keys()):
            tabs.set_title(index,title)

        # App description
        app_details = Accordion([HTML(app_des)])
        app_details.set_title(0, 'App Details')
        app_details.selected_index=None

        # Spinner for when data is loading
        self.widgets['spinner'] = HTML('''<i class="fa fa-spinner fa-spin" style="font-size:24px"></i>''')
        
        # Full App view
        self.children = [VBox([app_details, tabs])]


    def read_ui(self):
        '''
        Reads user inputs and stores them in a dictionary to use in other functions
        '''


        ui = {'idx_ticker' : self.widgets['idx_ticker'].value, 
              'idx_start_dt' : self.widgets['idx_start_dt'].value,
              'idx_end_dt' : self.widgets['idx_end_dt'].value, 
              'stock_ticker' : self.widgets['stock_ticker'].value,
              'stock_start_dt' : self.widgets['stock_start_dt'].value,
              'stock_end_dt' : self.widgets['stock_end_dt'].value,
              'stock_currency' : self.widgets['stock_currency'].value
             }


        return ui
    
    
##### RUN FUNCTIONS #####

    def index_run(self, *args):
        '''
        Get data and update view for the Index tab
        '''
        
        # Set up startup view
        start_view = list(self.widgets['index_view'].children)[:4]
        self.widgets['index_view'].children = start_view

        # Update view to show data is being fetched
        self.widgets['index_view'].children = start_view
        self.widgets['idx_btn_view'].children = [self.widgets['index_button'], self.widgets['spinner']]
        self.widgets['index_button'].disabled = True
        self.widgets['index_button'].description = 'Requesting Data...'
        self.widgets['index_button'].button_style = 'warning'


        try:
            
            # Get data
            df = self.get_idx_fut_data()
            oi_df = self.get_idx_open_int()
            hist_df = self.get_idx_hist()

#           # Create visualisations
            fig_curves = self.create_idx_curves(df)
            fig_bar = self.create_idx_bars(df)
            oi_chart = self.create_idx_oi_chart(oi_df)
            hist_chart = self.create_idx_hist_chart(hist_df)
            
            
            self.widgets['index_view'].children = start_view + [fig_curves, fig_bar, hist_chart, oi_chart]


        except Exception as e:
            err_msg = HTML('''<p style="color:red;" >{error}</p>'''.format(error = str(e)))
            self.widgets['index_view'].children = start_view + [err_msg]

        # Hide spinner and reset button to initial state
        self.widgets['idx_btn_view'].children = [self.widgets['index_button']]
        self.widgets['index_button'].disabled = False
        self.widgets['index_button'].description = 'Get Data'
        self.widgets['index_button'].button_style = 'Primary'
        
        
    def stock_run(self, *args):
        '''
        Get data and update view for the Single Stock tab
        '''
        
        # Set up startup view
        start_view = list(self.widgets['stock_view'].children[:5])
        self.widgets['stock_view'].children = start_view

        # Update view to show data is being fetched
        self.widgets['stock_view'].children = start_view
        self.widgets['stock_btn_view'].children = [self.widgets['stock_btn'], self.widgets['spinner']]
        self.widgets['stock_btn'].disabled = True
        self.widgets['stock_btn'].description = 'Requesting Data...'
        self.widgets['stock_btn'].button_style = 'warning'


        try:

            # Get data
            df1 = self.get_stock_fut_data()
            df2 = self.get_stock_est_data()
            df = pd.concat([df1, df2], axis=1)
            df = df.round(2)
            df_hist = self.get_stock_div_hist()
            price_df = self.get_stock_hist()

            # Create visualisations
            fig_curves = self.create_stock_curves(df)
            fig_bar = self.create_stock_bars(df)
            hist_chart = self.create_div_hist_chart(df_hist)
            price_chart = self.create_stock_chart(price_df)
            self.widgets['stock_view'].children = start_view + [fig_curves, fig_bar, hist_chart, price_chart]

        except Exception as e:
            err_msg = HTML('''<p style="color:red;" >{error}</p>'''.format(error = str(e)))
            self.widgets['stock_view'].children = start_view + [err_msg]


        # Hide spinner and reset button to initial state
        self.widgets['stock_btn_view'].children = [self.widgets['stock_btn']]
        self.widgets['stock_btn'].disabled = False
        self.widgets['stock_btn'].description = 'Get Data'
        self.widgets['stock_btn'].button_style = 'Primary'



##### GET INDEX DATA FUNCTIONS ##############


    def get_idx_fut_data(self):
        '''
        Pulls Index Dividend Futures data from BQL and processes response into a dataframe
        '''


        ui = self.read_ui() # Reads user inputs
        univ = self.bq.univ.futures(ui['idx_ticker']).filter(self.bq.data.fut_month_yr().left(3)=='DEC') # Set the universe to be only DEC futures for the selected index

        # Dictionary of fields to request with BQL
        fields = {'Tenor' : bq.data.fut_last_trade_dt().year(), # Year of expiry to be used as Tenor
                  str(ui['idx_start_dt']) : self.bq.data.px_settle(dates=ui['idx_start_dt']), # Price on Start Date
                  str(ui['idx_end_dt']) : self.bq.data.px_last(dates=ui['idx_end_dt'])} # Price on End Date


        with_params = {'fill' : 'prev',
                      'mode' : 'cached'}


        req = bql.Request(univ, fields, with_params = with_params) # Create request
        res = bq.execute(req) # Execute request
        
        
        df = pd.concat([fld.df()[fld.name] for fld in res], axis=1, sort=False) # Process response into dataframe
        df = df.set_index('Tenor').round(2) # Set the Tenor as index and round figures to 2 decimals
        df['Net Change'] = df[str(ui['idx_end_dt'])] - df[str(ui['idx_start_dt'])] # Add a column for net change between start and end date
        
        
        return df


    def get_idx_open_int(self):
        '''
        Pulls 5Y historical aggregate open interest for the Index
        '''


        ui = self.read_ui()


        root_ticker = ui['idx_ticker'].split('A Index')
        generic_ticker = str(root_ticker[0] + '1 Index')


        field = {'Open Interest' : bq.data.fut_agg_open_int(dates=bq.func.range('-5y', '0d')).dropna()}


        req = bql.Request(generic_ticker, field)
        res = bq.execute(req)


        df = res[0].df().set_index('DATE')


        return df
    
    
    def get_idx_hist(self):
        '''
        Get historical index close from start date to end date
        '''
        
        ui = self.read_ui()
        app_settings = self.get_model_settings()


        ticker = app_settings['index_mapping'][ui['idx_ticker']]


        field = {'Close': self.bq.data.px_last(dates=self.bq.func.range(ui['idx_start_dt'], ui['idx_end_dt'])).dropna()}


        req = bql.Request(ticker, field)
        res = bq.execute(req)
        
        
        df = res[0].df()
        df = df.set_index(['DATE'])
        
        
        return df            

    
    def get_idx_implied_points(self):
        '''
        Calculates bottom-up index points from single-stock broker estimates - not implemented
        '''
        
        
        ui = self.read_ui()
        
        
        index = self.get_model_settings()['index_mapping'][ui['idx_ticker']]
        univ = bq.univ.members(index)
       
        
        year = int(date.today().strftime('%Y'))
        years = range(year, year+11)
        
        
        shares = bq.data.id()['Positions'] 
        divisor = bq.data.indx_divisor().value(bq.univ.list(index))/10**6
        fields = [shares / divisor * bq.data.is_div_per_shr(fpt='a', fpr=str(year), currency='EUR').znav() for year in years]
        
        req = bql.Request(univ, fields)
        res = bq.execute(req)
        
        
        df = pd.concat([fld.df()[fld.name] for fld in res], axis = 1, sort = False)
        df = df.sum(axis=0)
        df = df.reset_index()
        df['Years'] = list(years)
        df = df.set_index('Years')
        
        
        return df
        
        
        
    
######## INDEX VIZ FUNCTIONS


    def create_idx_curves(self, df):
        '''
        Create dividend curves
        '''
        
        
        ui = self.read_ui()
        
        
        colours = ['Teal','LightBlue']

        #get name of index ticker selected to use in Chart Title
        app_settings = self.get_model_settings()
        

        index_lookup = {item: key for key, item in app_settings['index_info'].items()}


        traces = [go.Scatter(x = df.index, y = df[col], name = col) 
                  for col in df.columns if col not in ['Net Change']]


        fig = go.FigureWidget(data = traces, layout = {'template' : 'plotly_dark', 
                                                       'margin' : {'l':20, 'r':20, 't':20, 'b':20},
                                                       'colorway' : colours,
                                                       'title' : {'text' : index_lookup[ui['idx_ticker']] + ' Dividend Futures (Index Points)'},
                                                                 'title_x' : 0.5})
        

        fig.update_layout(legend_x = 0.01, 
                          legend_y = -0.05, 
                          title_pad = dict(b = 100, l = 100, r = 100, t = 100),
                          margin = dict(t = 50),
                          legend = dict(orientation='h'),
                          plot_bgcolor='rgba(33,33,33,33)',
                          paper_bgcolor='rgba(33,33,33,33)')
        
        
        fig.update_xaxes(dtick=1)


        return fig


    def create_idx_bars(self, df):
        '''
        Create bar chart showing net change
        '''


        traces = [go.Bar(x = df.index,
                             y = df[col],
                             name = col) for col in df.columns if col in ['Net Change']]


        fig = go.FigureWidget(data = traces,
                              layout = {'template': 'plotly_dark',
                                        'colorway' : ['LightBlue'],
                                        'margin': {'l':20, 'r':20, 't':20, 'b':20},
                                        'height': 120
                                       })
        
        
        fig.update_layout(plot_bgcolor = 'rgba(33,33,33,33)',
                          paper_bgcolor = 'rgba(33,33,33,33)',
                          legend_y = -0.45,
                          legend_x = 0.01,
                          legend = dict(orientation = 'h'),
                          showlegend = True)


        return fig


    def create_idx_oi_chart(self, df):
        '''
        Create line chart with historical index open interest data from get_idx_open_int()
        '''


        ui = self.read_ui()
        
        
        #Get name of index to use in Chart Title
        app_settings = self.get_model_settings()
        index_lookup = {item: key for key, item in app_settings['index_info'].items()}


        traces = go.Scatter(x = df.index,
                            y = df['Open Interest'])


        fig = go.FigureWidget(data = traces,
                              layout = {'template' : 'plotly_dark',
                                        'colorway' : ['Teal'],
                                        'title' : {'text' : index_lookup[ui['idx_ticker']] + ' Dividend Futures Aggregate Open Interest (5Y)'},
                                        'title_x' : 0.5,
                                        'height' : 350,
                                        'legend_y' : -0.2,
                                        'margin' : {'l':20, 'r':20, 't':50, 'b':50}})
        
        
        fig.update_layout(plot_bgcolor = 'rgba(33,33,33,33)',
                          paper_bgcolor = 'rgba(33,33,33,33)')


        return fig
    
    
    def create_idx_hist_chart(self, df):
        '''
        Create line chart for historical index closing prices
        '''
        
        
        ui = self.read_ui()
        app_settings = self.get_model_settings()
        index_lookup = {item: key for key, item in app_settings['index_info'].items()}


        traces = go.Scatter(x = df.index,
                            y = df['Close'])
        
        
        fig = go.FigureWidget(data = traces,
                              layout = {'template' : 'plotly_dark',
                                        'colorway' : ['Teal'],
                                        'title' : {'text' : index_lookup[ui['idx_ticker']] + ' Historical Closing Price '},
                                        'title_x' : 0.5,
                                        'height' : 350,
                                        'legend_y' : -0.2,
                                        'margin' : {'l':20, 'r':20, 't':50, 'b':50}})
        
        
        fig.update_layout(plot_bgcolor = 'rgba(33,33,33,33)',
                          paper_bgcolor = 'rgba(33,33,33,33)')


        return fig



    

##### SINGLE STOCK GET DATA FUNCTIONS

    def get_stock_fut_data(self):
        '''
        Pulls dividend futures data for selected ticker and dates
        '''


        ui = self.read_ui()
        univ = bq.univ.futures(ui['stock_ticker'])

        # Define filters to screen for liquid single stock dividend futures
        filters = {'exch' : bq.data.exch_code()=='GR',
                   'sec_typ' : bq.data.security_typ()=='SINGLE STOCK DIVIDEND FUTURE',
                   'month' : bq.data.fut_last_trade_dt().month()==12,
                   }

        
        # Group px_last() by year of expiry and average to deal with companies with more than one active dividend future per year
        fields = {'FUT ' + str(ui['stock_start_dt']) : bq.data.px_settle(dates=ui['stock_start_dt']).group(bq.data.fut_last_trade_dt().year()).avg()['value'], 
                  'FUT ' + str(ui['stock_end_dt']) : bq.data.px_last(dates=ui['stock_end_dt']).group(bq.data.fut_last_trade_dt().year()).avg()['value']}
        

        with_params = {'fill' : 'prev',
                       'mode' : 'cached',
                       'currency' : ui['stock_currency']}

        
        univ = univ.filter(filters['exch'].and_(filters['sec_typ']).and_(filters['month']))


        req = bql.Request(univ, fields, with_params = with_params)
        res = bq.execute(req)


        df = pd.concat([fld.df()[fld.name] for fld in res], axis=1, sort=False)
        df['Net Chg - Futures'] = df['FUT ' + str(ui['stock_end_dt'])] - df['FUT ' + str(ui['stock_start_dt'])]
        df['Net Chg - Futures'] = df['Net Chg - Futures'].round(2)


        return df   


    def get_stock_est_data(self):
        '''
        Pulls broker estimates for dividend per share from current year (N) to N+5
        '''
        ui = self.read_ui()
        year = ui['stock_start_dt'].year


        fields = {'Tenor' : self.bq.data.is_div_per_shr(as_of_date=ui['stock_start_dt'], fpt='a', fpr=self.bq.func.range(year, year+5))['PERIOD_END_DATE'].year(), 
                  'EST ' + str(ui['stock_start_dt']) : self.bq.data.is_div_per_shr(as_of_date=ui['stock_start_dt'], fpt='a', fpr=self.bq.func.range(year, year+5)), 
                  'EST ' + str(ui['stock_end_dt']) : self.bq.data.is_div_per_shr(as_of_date=ui['stock_end_dt'], fpt='a', fpr=self.bq.func.range(year, year+5))
                 }


        with_params = {'fill': 'prev',
                       'currency': ui['stock_currency']} 


        req = bql.Request(ui['stock_ticker'], fields, with_params=with_params)
        res = bq.execute(req)


        df = pd.concat([fld.df()[fld.name] for fld in res], axis=1, sort=False)
        df = df.set_index('Tenor')
        df['Net Chg - Estimates'] = (df['EST ' + str(ui['stock_end_dt'])] - df['EST ' + str(ui['stock_start_dt'])]).round(2)


        return df


    def get_stock_div_hist(self):
        '''
        Pulls annual dividends for the past 20 years 
        '''


        ui = self.read_ui()
        # ticker = self.read_stock_ui()['Ticker']
        divs = bq.data.is_div_per_shr(fpt='a',fpo=bq.func.range('-25y', '0y')).znav()


        field = {'Dividends': divs.group(divs['PERIOD_END_DATE'].year())}


        with_params = {'fill': 'prev',
                       'mode': 'cached',
                      'currency': ui['stock_currency']}


        req = bql.Request(ui['stock_ticker'], field, with_params = with_params)
        res = bq.execute(req)


        df = pd.concat([fld.df()[fld.name] for fld in res], axis=1, sort=False)
        df['Dividends'] = df['Dividends'].round(2)
        

        return df
    
    
    def get_stock_hist(self):
        '''
        Pulls daily closing price from start date to end date for Single Stock
        '''
        
        
        ui = self.read_ui()
        
        field = {'Close': self.bq.data.px_last(dates = self.bq.func.range(ui['stock_start_dt'], ui['stock_end_dt'])).dropna()}
        
        
        with_params = {'fill': 'prev',
                      'mode': 'cached',
                      'currency': ui['stock_currency']}
        
        
        req = bql.Request(ui['stock_ticker'], field, with_params = with_params)
        res = bq.execute(req)
        
        
        df = res[0].df()
        df = df.set_index(['DATE'])
        
        
        return df      
        
    

##### SINGLE STOCK VISUALISTION FUNCTIONS
   

    def create_stock_curves(self, df):
        '''
        Create single-stock dividend curves
        '''


        ui = self.read_ui()
        
        
        colours = ['Teal','LightBlue', 'Aqua', 'CornflowerBlue']
        
        
        traces = [go.Scatter(x = df.index, y = df[col], name = col) 
                  for col in df.columns if col not in ['Net Chg - Futures'] and col not in ['Net Chg - Estimates']]


        fig = go.FigureWidget(data = traces, layout = {'template' : 'plotly_dark', 
                                                       'margin' : {'l':20, 'r':20, 't':20, 'b':20},
                                                       'height' : 450,
                                                       'colorway' : colours,
                                                       'title' : 
                                                       {'text' : self.get_idx_members()[ui['stock_ticker']] + ' Dividend Futures vs Consensus (' + ui['stock_currency'] + ')'},
                                                        'title_x' : 0.5})
        
        
        fig.update_layout(legend_x = 0.01, 
                          legend_y = -0.05, 
                          title_pad = dict(b = 100, l = 100, r = 100, t = 100),
                          margin = dict(t = 50),
                          legend = dict(orientation='h'),
                          plot_bgcolor='rgba(33,33,33,33)', paper_bgcolor='rgba(33,33,33,33)')
        
        
        fig.update_xaxes(dtick=1)
        
        
        return fig


    def create_stock_bars(self, df):
        '''
        Create single-stock bar charts showing net change
        '''
        
        
        colours = colours = ['Teal', 'Aqua']


        traces = [go.Bar(x = df.index,
                         y = df[col],
                         name = col) for col in df.columns if col in ['Net Chg - Futures'] or col in ['Net Chg - Estimates']]


        fig = go.FigureWidget(data = traces,
                              layout = {'template' : 'plotly_dark', 
                                        'margin' : {'l':20, 'r':20, 't':20, 'b':80},
                                        'colorway' : colours,
                                        'height' : 180})
        
        
        fig.update_layout(legend_y = -0.2,
                          legend_x = 0.01,
                          legend = dict(orientation = 'h'),
                          plot_bgcolor = 'rgba(33,33,33,33)',
                          paper_bgcolor = 'rgba(33,33,33,33)')


        return fig


    def create_div_hist_chart(self, df):
        '''
        Create 25-year historical dividends chart
        '''


        ui = self.read_ui()


        traces = go.Scatter(x = [year[:4] for year in list(df.index)],
                            y = df['Dividends'])


        fig = go.FigureWidget(data = traces,
                              layout = {'template' : 'plotly_dark',
                                        'colorway' : ['#919191'],
                                        'title' : 
                                        {'text' : self.get_idx_members()[ui['stock_ticker']] + ' Historical Dividends - Annual - 25Y (' + ui['stock_currency'] + ')'},
                                        'title_x' : 0.5})
        
        
        fig.update_layout(plot_bgcolor='rgba(33,33,33,33)', paper_bgcolor='rgba(33,33,33,33)')


        return fig
    
    
    def create_stock_chart(self, df):
        '''
        Create line chart for Single Stock historical closing price from start date to end date
        '''

        
        ui = self.read_ui()
        app_settings = self.get_model_settings()
        index_lookup = {item: key for key, item in app_settings['index_info'].items()}
       
        
        traces = go.Scatter(x = df.index,
                            y = df['Close'])
        
        
        fig = go.FigureWidget(data = traces,
                              layout = {'template' : 'plotly_dark',
                                        'colorway' : ['Teal'],
                                        'title' : 
                                        {'text' : self.get_idx_members()[ui['stock_ticker']] + ' Historical Closing Price (' + ui['stock_currency'] + ')'},
                                        'title_x' : 0.5,
                                        'height' : 350,
                                        'legend_y' : -0.2,
                                        'margin' : {'l':20, 'r':20, 't':50, 'b':50}})
        
        
        fig.update_layout(plot_bgcolor = 'rgba(33,33,33,33)',
                          paper_bgcolor = 'rgba(33,33,33,33)')


        return fig

    
