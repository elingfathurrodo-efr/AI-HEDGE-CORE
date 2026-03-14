//+------------------------------------------------------------------+
//| SEA-TO Executor for MetaTrader 5                                 |
//| Light-weight signal executor - Brain is on GitHub                |
//+------------------------------------------------------------------+
#property copyright "SEA-TO Project"
#property link      "https://github.com/elingfathurrodo-efr/AI-HEDGE-CORE"
#property version   "1.00"
#property strict

// Input parameters
input string   GitHub_Raw_URL = "https://raw.githubusercontent.com/elingfathurrodo-efr/AI-HEDGE-CORE/main/";
input string   Signal_Endpoint = "API/signal.json";
input int      Check_Interval_Seconds = 10;
input string   Trading_Symbol = "XAUUSD";
input double   Risk_Percent = 2.0;
input bool     Use_Ghost_SL = true;

// Global variables
string         g_token = "";  // Will be set via WebRequest header
int            g_magic = 123456;
bool           g_locked_fund_active = false;
double         g_locked_fund_amount = 0;
double         g_session_start_equity = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("🧠 SEA-TO Executor Initialized");
   Print("🔗 Connecting to GitHub Brain...");
   
   // Set WebRequest permission for GitHub
   string url;
   StringConcatenate(url, GitHub_Raw_URL, Signal_Endpoint);
   
   g_session_start_equity = AccountInfoDouble(ACCOUNT_EQUITY);
   
   // Timer untuk check signal
   EventSetTimer(Check_Interval_Seconds);
   
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   Print("🛑 SEA-TO Executor Stopped");
}

//+------------------------------------------------------------------+
//| Timer function                                                   |
//+------------------------------------------------------------------+
void OnTimer()
{
   CheckAndExecuteSignals();
   CheckCapitalProtection();
}

//+------------------------------------------------------------------+
//| Fetch and execute signals from GitHub                            |
//+------------------------------------------------------------------+
void CheckAndExecuteSignals()
{
   string url;
   StringConcatenate(url, GitHub_Raw_URL, Signal_Endpoint);
   
   char data[], result[];
   string headers;
   int res;
   
   // WebRequest to GitHub
   res = WebRequest("GET", url, headers, 5000, data, result, headers);
   
   if(res != 200)
   {
      Print("❌ Failed to fetch signal. Error: ", res);
      return;
   }
   
   string json = CharArrayToString(result);
   
   // Parse JSON sederhana (dalam produksi gunakan library JSON)
   if(StringFind(json, "\"action\":\"BUY\"") != -1)
   {
      ExecuteTrade(ORDER_TYPE_BUY);
   }
   else if(StringFind(json, "\"action\":\"SELL\"") != -1)
   {
      ExecuteTrade(ORDER_TYPE_SELL);
   }
}

//+------------------------------------------------------------------+
//| Execute trade with anti-stacking                                 |
//+------------------------------------------------------------------+
void ExecuteTrade(ENUM_ORDER_TYPE order_type)
{
   // Check anti-stacking
   if(IsPriceLayerExists(SymbolInfoDouble(_Symbol, SYMBOL_BID)))
   {
      Print("⚠️ Anti-Stacking: Position exists at this level");
      return;
   }
   
   // Check locked fund
   if(g_locked_fund_active)
   {
      double available = AccountInfoDouble(ACCOUNT_EQUITY) - g_locked_fund_amount;
      if(available <= 0)
      {
         Print("🔒 Locked Fund Protection: No available capital");
         return;
      }
   }
   
   double lot = CalculateLotSize();
   double price = (order_type == ORDER_TYPE_BUY) ? 
                  SymbolInfoDouble(_Symbol, SYMBOL_ASK) : 
                  SymbolInfoDouble(_Symbol, SYMBOL_BID);
   
   // Ghost SL (not sent to broker)
   double ghost_sl = CalculateGhostSL(order_type, price);
   
   MqlTradeRequest request = {};
   MqlTradeResult result = {};
   
   request.action = TRADE_ACTION_DEAL;
   request.symbol = _Symbol;
   request.volume = lot;
   request.type = order_type;
   request.price = price;
   request.deviation = 10;
   request.magic = g_magic;
   request.comment = "SEA-TO";
   
   // TP visible, SL ghost (managed by EA)
   request.tp = CalculateTakeProfit(order_type, price);
   request.sl = 0;  // Ghost SL - not sent to broker
   
   if(!OrderSend(request, result))
   {
      Print("❌ Order failed: ", GetLastError());
      return;
   }
   
   // Simpan Ghost SL ke file/variabel untuk monitoring
   SaveGhostSL(result.order, ghost_sl);
   
   Print("✅ Trade executed: ", order_type, " @ ", price, " Ghost SL: ", ghost_sl);
}

//+------------------------------------------------------------------+
//| Check for existing positions at price layer                      |
//+------------------------------------------------------------------+
bool IsPriceLayerExists(double current_price)
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      if(PositionGetInteger(POSITION_MAGIC) != g_magic) continue;
      
      double open_price = PositionGetDouble(POSITION_PRICE_OPEN);
      double distance = MathAbs(current_price - open_price) / _Point;
      
      if(distance < 50)  // 5 pips for XAUUSD (50 points)
      {
         return true;
      }
   }
   return false;
}

//+------------------------------------------------------------------+
//| Calculate Ghost Stop Loss                                        |
//+------------------------------------------------------------------+
double CalculateGhostSL(ENUM_ORDER_TYPE type, double entry_price)
{
   double atr = iATR(_Symbol, PERIOD_CURRENT, 14);
   double sl_distance = atr * 1.5;  // 1.5x ATR
   
   if(type == ORDER_TYPE_BUY)
      return entry_price - sl_distance;
   else
      return entry_price + sl_distance;
}

//+------------------------------------------------------------------+
//| Capital Protection: 2x Rule                                      |
//+------------------------------------------------------------------+
void CheckCapitalProtection()
{
   double current_equity = AccountInfoDouble(ACCOUNT_EQUITY);
   double profit_pct = (current_equity - g_session_start_equity) / g_session_start_equity;
   
   // Jika profit 100%, kunci modal
   if(profit_pct >= 1.0 && !g_locked_fund_active)
   {
      g_locked_fund_amount = g_session_start_equity;
      g_locked_fund_active = true;
      
      Print("🔒 LOCKED FUND ACTIVATED: ", g_locked_fund_amount);
      Print("💰 Profit locked until next session");
      
      // Kirim notifikasi ke GitHub (opsional)
      NotifyGitHub("LOCKED_FUND", g_locked_fund_amount);
   }
}

//+------------------------------------------------------------------+
//| Dynamic Trailing Stop                                            |
//+------------------------------------------------------------------+
void CheckTrailingStop()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      
      double open_price = PositionGetDouble(POSITION_PRICE_OPEN);
      double current_price = PositionGetDouble(POSITION_PRICE_CURRENT);
      double profit_pct = MathAbs(current_price - open_price) / open_price;
      
      // Dynamic trailing: 10% -> 95%
      double lock_level = 0.10 + (profit_pct * 0.85);  // Naik hingga 95%
      lock_level = MathMin(lock_level, 0.95);
      
      double locked_profit = open_price + (open_price * lock_level * 
                            (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY ? 1 : -1));
      
      // Update Ghost SL
      UpdateGhostSL(ticket, locked_profit);
   }
}

//+------------------------------------------------------------------+
//| Helper functions                                                 |
//+------------------------------------------------------------------+
double CalculateLotSize()
{
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   if(g_locked_fund_active)
      balance -= g_locked_fund_amount;
   
   double risk_amount = balance * (Risk_Percent / 100);
   double tick_value = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double sl_points = 500;  // 50 pips default
   
   return NormalizeDouble(risk_amount / (sl_points * tick_value), 2);
}

double CalculateTakeProfit(ENUM_ORDER_TYPE type, double entry)
{
   double atr = iATR(_Symbol, PERIOD_CURRENT, 14);
   if(type == ORDER_TYPE_BUY)
      return entry + (atr * 2);
   else
      return entry - (atr * 2);
}

void SaveGhostSL(ulong ticket, double sl_price)
{
   // Simpan ke file atau global variable
   // Implementasi tergantung kebutuhan
}

void UpdateGhostSL(ulong ticket, double new_sl)
{
   // Update Ghost SL
}

void NotifyGitHub(string event, double value)
{
   // Kirim webhook ke GitHub Actions
}

//+------------------------------------------------------------------+

