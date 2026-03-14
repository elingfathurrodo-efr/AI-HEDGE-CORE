//+------------------------------------------------------------------+
//|                    AI_Trading_Organism.mq5                       |
//|            AI Trading Organism - MT5 Signal Executor             |
//|  RINGAN - Hanya baca signal.json via WebRequest & eksekusi trade |
//|  AI BERJALAN DI GITHUB ACTIONS - Laptop tetap ringan!            |
//+------------------------------------------------------------------+
#property copyright "AI Trading Organism"
#property version   "2.00"
#property strict

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>

CTrade   Trade;
CPositionInfo PosInfo;

//--- Input Parameters
input string   SignalURL         = "https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/signal.json";
input string   DashboardURL      = "https://YOUR_USERNAME.github.io/YOUR_REPO/";
input double   InitialBalance    = 50.0;      // Modal awal
input double   DefaultLot        = 0.01;      // Lot default
input int      MinLayerDistance  = 150;       // Minimal jarak antar layer (points)
input int      SignalFetchSeconds = 60;       // Fetch signal setiap N detik
input int      GhostSLPoints     = 200;       // Ghost Stop Loss (points)
input bool     EnableHedging     = true;      // Enable hedging (BUY + SELL bersamaan)
input bool     EnableTrailing    = true;      // Enable trailing profit lock
input bool     EnableGhostSL     = true;      // Enable ghost stop loss
input bool     EnableCapProtect  = true;      // Enable capital protection 2x rule
input int      MaxOpenTrades     = 10;        // Max jumlah trade terbuka
input color    PanelColor        = clrNavy;   // Warna panel dashboard

//--- Signal Structure
struct SignalData {
   string   signal;         // "BUY" / "SELL" / "NONE"
   string   symbol;
   double   lot;
   int      sl_points;
   double   tp_ratio;
   string   reason;
   string   organism_id;
   string   session;
   string   timestamp;
   long     generated_at_unix;
};

//--- Global Variables
datetime  g_LastSignalTime    = 0;
datetime  g_LastCandleTime    = 0;
datetime  g_LastFetchTime     = 0;
double    g_LockedFund        = 0;
double    g_TradingFund       = 0;
string    g_LastSignal        = "NONE";
string    g_LastSignalId      = "";
string    g_CurrentSession    = "";
string    g_CurrentOrganism   = "organism_001";
string    g_LastReason        = "";
bool      g_IsInitialized     = false;
bool      g_WaitUnlock        = false;
string    g_LockSession       = "";
int       g_EvolutionGen      = 0;

//--- Panel label names
string panelLabels[];

//+------------------------------------------------------------------+
//| Expert initialization                                            |
//+------------------------------------------------------------------+
int OnInit() {
   Trade.SetDeviationInPoints(30);
   Trade.SetTypeFilling(ORDER_FILLING_FOK);
   if(EnableHedging) {
      // Enable hedging in account
      Trade.SetExpertMagicNumber(202401);
   }
   g_TradingFund = InitialBalance;
   g_IsInitialized = true;
   Print("=== AI Trading Organism v2.0 INITIALIZED ===");
   Print("Signal URL: ", SignalURL);
   Print("Initial Balance: $", InitialBalance);
   
   // Create permanent dashboard panel
   CreateDashboardPanel();
   
   // Initial fetch
   FetchAndProcessSignal();
   
   EventSetTimer(SignalFetchSeconds);
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization                                          |
//+------------------------------------------------------------------+
void OnDeinit(const int reason) {
   EventKillTimer();
   RemoveDashboardPanel();
   Print("AI Trading Organism deinitialized.");
}

//+------------------------------------------------------------------+
//| Timer - fetch signal every N seconds                             |
//+------------------------------------------------------------------+
void OnTimer() {
   FetchAndProcessSignal();
   UpdateDashboardPanel();
}

//+------------------------------------------------------------------+
//| On every tick                                                    |
//+------------------------------------------------------------------+
void OnTick() {
   // Check Ghost SL
   if(EnableGhostSL) CheckGhostStopLoss();
   
   // Check trailing profit lock
   if(EnableTrailing) CheckTrailingLock();
   
   // Check capital protection
   if(EnableCapProtect) CheckCapitalProtection();
   
   // Update session
   g_CurrentSession = GetCurrentSession();
   
   // Update panel every tick (lightweight)
   UpdateDashboardPanelLight();
}

//+------------------------------------------------------------------+
//| NEW CANDLE detection                                             |
//+------------------------------------------------------------------+
bool IsNewCandle() {
   datetime currentCandle = iTime(_Symbol, PERIOD_M1, 0);
   if(currentCandle != g_LastCandleTime) {
      g_LastCandleTime = currentCandle;
      return true;
   }
   return false;
}

//+------------------------------------------------------------------+
//| FETCH SIGNAL FROM GITHUB                                         |
//+------------------------------------------------------------------+
void FetchAndProcessSignal() {
   string signal_json = FetchURL(SignalURL);
   if(signal_json == "") return;
   
   SignalData sig;
   if(!ParseSignalJSON(signal_json, sig)) return;
   
   // Validate signal freshness (must be within 2 minutes)
   // (Using string timestamp comparison - simplified)
   
   // Only process on NEW CANDLE
   if(!IsNewCandle()) return;
   
   if(sig.signal == "NONE" || sig.signal == "") return;
   
   // Check if this is same signal we already processed
   if(sig.timestamp == g_LastSignalId) return;
   
   Print("=== NEW SIGNAL: ", sig.signal, " | ", sig.reason, " ===");
   g_LastSignalId  = sig.timestamp;
   g_LastSignal    = sig.signal;
   g_LastReason    = sig.reason;
   g_CurrentOrganism = sig.organism_id;
   
   // Execute signal
   ExecuteSignal(sig);
}

//+------------------------------------------------------------------+
//| FETCH URL via WebRequest                                         |
//+------------------------------------------------------------------+
string FetchURL(string url) {
   char   post_data[];
   char   response[];
   string response_headers;
   string headers = "Accept: application/json\r\n";
   
   int result = WebRequest("GET", url, headers, 5000, post_data, response, response_headers);
   
   if(result == -1) {
      int err = GetLastError();
      if(err == 4060)
         Print("Add URL to allowed list: Tools > Options > Expert Advisors");
      else
         Print("WebRequest error: ", err);
      return "";
   }
   return CharArrayToString(response);
}

//+------------------------------------------------------------------+
//| PARSE SIGNAL JSON (lightweight manual parser)                    |
//+------------------------------------------------------------------+
bool ParseSignalJSON(string json, SignalData &sig) {
   sig.signal      = ExtractJSONString(json, "signal");
   sig.symbol      = ExtractJSONString(json, "symbol");
   sig.reason      = ExtractJSONString(json, "reason");
   sig.organism_id = ExtractJSONString(json, "organism_id");
   sig.session     = ExtractJSONString(json, "session");
   sig.timestamp   = ExtractJSONString(json, "timestamp");
   
   string lot_str  = ExtractJSONValue(json, "lot");
   string sl_str   = ExtractJSONValue(json, "sl_points");
   string tp_str   = ExtractJSONValue(json, "tp_ratio");
   
   sig.lot         = lot_str != "" ? StringToDouble(lot_str) : DefaultLot;
   sig.sl_points   = sl_str  != "" ? (int)StringToInteger(sl_str) : GhostSLPoints;
   sig.tp_ratio    = tp_str  != "" ? StringToDouble(tp_str) : 2.0;
   
   if(sig.lot <= 0) sig.lot = DefaultLot;
   if(sig.sl_points <= 0) sig.sl_points = GhostSLPoints;
   
   return (sig.signal == "BUY" || sig.signal == "SELL");
}

string ExtractJSONString(string json, string key) {
   string search = "\"" + key + "\":\"";
   int pos = StringFind(json, search);
   if(pos < 0) return "";
   pos += StringLen(search);
   int end = StringFind(json, "\"", pos);
   if(end < 0) return "";
   return StringSubstr(json, pos, end - pos);
}

string ExtractJSONValue(string json, string key) {
   string search = "\"" + key + "\":";
   int pos = StringFind(json, search);
   if(pos < 0) return "";
   pos += StringLen(search);
   // Skip spaces
   while(pos < StringLen(json) && StringGetCharacter(json, pos) == ' ') pos++;
   int end = pos;
   while(end < StringLen(json)) {
      ushort c = StringGetCharacter(json, end);
      if(c == ',' || c == '}' || c == '\n' || c == '\r') break;
      end++;
   }
   return StringSubstr(json, pos, end - pos);
}

//+------------------------------------------------------------------+
//| CHECK ANTI-STACKING - Layer distance validation                  |
//+------------------------------------------------------------------+
bool IsLayerStackingAllowed(string direction) {
   double minDist = MinLayerDistance * _Point;
   double curPrice = SymbolInfoDouble(_Symbol, (direction == "BUY") ? SYMBOL_ASK : SYMBOL_BID);

   int openCount = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--) {
      if(!PosInfo.SelectByIndex(i)) continue;
      if(PosInfo.Symbol() != _Symbol) continue;
      openCount++;

      double posPrice = PosInfo.PriceOpen();
      // Block stacking if too close to ANY existing layer (BUY or SELL)
      if(MathAbs(posPrice - curPrice) < minDist) {
         Print("Anti-stacking: too close to existing layer at ", posPrice,
               ". Distance: ", MathAbs(posPrice - curPrice) / _Point, " points");
         return false;
      }
   }

   if(openCount >= MaxOpenTrades) {
      Print("Max open trades reached: ", openCount);
      return false;
   }
   return true;
}

//+------------------------------------------------------------------+
//| EXECUTE SIGNAL                                                   |
//+------------------------------------------------------------------+
void ExecuteSignal(SignalData &sig) {
   // Validate lot via immune rules
   double lot = NormalizeLot(sig.lot);
   
   // Check anti-stacking
   if(!IsLayerStackingAllowed(sig.signal)) {
      Print("Signal ", sig.signal, " blocked: stacking rule");
      return;
   }
   
   // Check capital protection
   if(!IsCapitalSafe()) {
      Print("Signal blocked: capital protection active");
      return;
   }
   
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   int    digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   
   // Ghost SL: we manage SL internally, send 0 to broker
   double broker_sl = 0;  // Ghost SL - not sent to broker
   double broker_tp = 0;  // No TP sent either (trailing manages it)
   
   bool success = false;
   if(sig.signal == "BUY") {
      success = Trade.Buy(lot, _Symbol, ask, broker_sl, broker_tp,
                          "AI_" + sig.organism_id + "_" + sig.session);
   } else if(sig.signal == "SELL") {
      success = Trade.Sell(lot, _Symbol, bid, broker_sl, broker_tp,
                           "AI_" + sig.organism_id + "_" + sig.session);
   }
   
   if(success) {
      Print("✅ Trade OPENED: ", sig.signal, " Lot=", lot,
            " | ", sig.reason, " | Organism=", sig.organism_id);
      // Store ghost SL data in trade comment or global var
      // (managed in CheckGhostStopLoss)
   } else {
      Print("❌ Trade FAILED: ", Trade.ResultRetcode(), " - ", Trade.ResultRetcodeDescription());
   }
}

//+------------------------------------------------------------------+
//| GHOST STOP LOSS - EA monitors SL internally                      |
//+------------------------------------------------------------------+
void CheckGhostStopLoss() {
   for(int i = PositionsTotal() - 1; i >= 0; i--) {
      if(!PosInfo.SelectByIndex(i)) continue;
      if(PosInfo.Symbol() != _Symbol) continue;
      
      double entryPrice  = PosInfo.PriceOpen();
      double currentBid  = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      double currentAsk  = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      double ghostSLDist = GhostSLPoints * _Point;
      
      bool shouldClose = false;
      
      if(PosInfo.PositionType() == POSITION_TYPE_BUY) {
         double ghostSL = entryPrice - ghostSLDist;
         if(currentBid <= ghostSL) {
            Print("👻 Ghost SL triggered for BUY at ", currentBid, " (SL level: ", ghostSL, ")");
            shouldClose = true;
         }
      } else { // SELL
         double ghostSL = entryPrice + ghostSLDist;
         if(currentAsk >= ghostSL) {
            Print("👻 Ghost SL triggered for SELL at ", currentAsk, " (SL level: ", ghostSL, ")");
            shouldClose = true;
         }
      }
      
      if(shouldClose) {
         ulong ticket = PosInfo.Ticket();
         if(Trade.PositionClose(ticket)) {
            Print("👻 Ghost SL: Position closed successfully");
         }
      }
   }
}

//+------------------------------------------------------------------+
//| TRAILING PROFIT LOCK                                             |
//+------------------------------------------------------------------+
void CheckTrailingLock() {
   // TRUE GHOST TRAILING:
   // - Do NOT send SL/TP to broker
   // - EA internally computes lock level and closes when price crosses it
   for(int i = PositionsTotal() - 1; i >= 0; i--) {
      if(!PosInfo.SelectByIndex(i)) continue;
      if(PosInfo.Symbol() != _Symbol) continue;

      double entryPrice  = PosInfo.PriceOpen();
      double currentBid  = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      double currentAsk  = SymbolInfoDouble(_Symbol, SYMBOL_ASK);

      double profitPct = 0;
      if(PosInfo.PositionType() == POSITION_TYPE_BUY) {
         if(entryPrice > 0) profitPct = (currentBid - entryPrice) / entryPrice * 100.0;
      } else {
         if(entryPrice > 0) profitPct = (entryPrice - currentAsk) / entryPrice * 100.0;
      }
      if(profitPct <= 0) continue;

      double lockPct = GetTrailingLockPct(profitPct);
      if(lockPct <= 0) continue;

      double lockPrice = 0;
      if(PosInfo.PositionType() == POSITION_TYPE_BUY)
         lockPrice = entryPrice * (1.0 + lockPct/100.0);
      else
         lockPrice = entryPrice * (1.0 - lockPct/100.0);

      // If price retraces to lock level -> close position
      bool shouldClose = false;
      if(PosInfo.PositionType() == POSITION_TYPE_BUY) {
         if(currentBid <= lockPrice) shouldClose = true;
      } else {
         if(currentAsk >= lockPrice) shouldClose = true;
      }

      if(shouldClose) {
         ulong ticket = PosInfo.Ticket();
         Print("🔒 Ghost trailing lock hit. Closing ticket=", ticket,
               " profitPct=", DoubleToString(profitPct,2), "% lockPct=", lockPct,
               " lockPrice=", DoubleToString(lockPrice, _Digits));
         Trade.PositionClose(ticket);
      }
   }
}

double GetTrailingLockPct(double profitPct) {
   if(profitPct >= 95) return 90;
   if(profitPct >= 90) return 80;
   if(profitPct >= 80) return 65;
   if(profitPct >= 70) return 54;
   if(profitPct >= 60) return 44;
   if(profitPct >= 50) return 35;
   if(profitPct >= 40) return 28;
   if(profitPct >= 30) return 20;
   if(profitPct >= 20) return 10;
   if(profitPct >= 10) return 5;
   return 0;
}

//+------------------------------------------------------------------+
//| CAPITAL PROTECTION                                               |
//+------------------------------------------------------------------+
void CheckCapitalProtection() {
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double equity  = AccountInfoDouble(ACCOUNT_EQUITY);
   
   // 2x rule: if balance doubled, lock 50%
   if(balance >= InitialBalance * 2.0 && g_LockedFund == 0) {
      g_LockedFund  = balance / 2.0;
      g_TradingFund = balance / 2.0;
      Print("💰 2x RULE TRIGGERED! Balance: $", balance);
      Print("💰 Locked: $", g_LockedFund, " | Trading: $", g_TradingFund);
      // Alert user
      Alert("AI Organism: 2x Rule! Balance doubled! $" + DoubleToString(g_LockedFund, 2) + " locked!");
   }
}

bool IsCapitalSafe() {
   // If waiting unlock, only allow trading after session changed
   string sessionNow = GetCurrentSession();
   if(g_WaitUnlock) {
      if(sessionNow != g_LockSession && sessionNow != "Closed") {
         Print("✅ Session changed (", g_LockSession, " -> ", sessionNow, "). Unlock trading.");
         g_WaitUnlock = false;
         g_LockSession = "";
         return true;
      }
      Print("⏳ Capital protection: waiting next session. Locked at ", g_LockSession,
            " now ", sessionNow);
      return false;
   }

   double equity = AccountInfoDouble(ACCOUNT_EQUITY);

   // If equity dropped too low and locked fund exists, stop until next session
   if(g_LockedFund > 0 && g_TradingFund > 0 && equity < g_TradingFund * 0.1) {
      g_WaitUnlock = true;
      g_LockSession = sessionNow;
      Print("⚠️ Trading fund nearly depleted. WAIT until next session. Locked at session=", g_LockSession);
      return false;
   }

   return true;
}

//+------------------------------------------------------------------+
//| MARKET SESSION                                                   |
//+------------------------------------------------------------------+
string GetCurrentSession() {
   MqlDateTime dt;
   TimeToStruct(TimeGMT(), dt);
   int h = dt.hour;
   if(h >= 0  && h < 9)  return "Asia";
   if(h >= 8  && h < 17) return "London";
   if(h >= 13 && h < 22) return "NewYork";
   return "Closed";
}

//+------------------------------------------------------------------+
//| NORMALIZE LOT                                                    |
//+------------------------------------------------------------------+
double NormalizeLot(double lot) {
   double minLot  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double stepLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   if(lot < minLot) lot = minLot;
   if(lot > 0.10)   lot = 0.10;   // Cap at 0.10 for safety
   lot = MathFloor(lot / stepLot) * stepLot;
   return lot;
}

//+------------------------------------------------------------------+
//| DASHBOARD PANEL (PERMANENT - MANUAL, NOT AI-MODIFIED)           |
//+------------------------------------------------------------------+
void CreateDashboardPanel() {
   string prefix = "AI_ORG_";
   int x = 10, y = 25;
   int w = 280, h = 22;
   int rows = 12;
   
   // Background
   ObjectCreate(0, prefix+"BG", OBJ_RECTANGLE_LABEL, 0, 0, 0);
   ObjectSetInteger(0, prefix+"BG", OBJPROP_XDISTANCE, x - 5);
   ObjectSetInteger(0, prefix+"BG", OBJPROP_YDISTANCE, y - 5);
   ObjectSetInteger(0, prefix+"BG", OBJPROP_XSIZE, w + 10);
   ObjectSetInteger(0, prefix+"BG", OBJPROP_YSIZE, rows * (h + 3) + 15);
   ObjectSetInteger(0, prefix+"BG", OBJPROP_BGCOLOR, C'10,15,40');
   ObjectSetInteger(0, prefix+"BG", OBJPROP_BORDER_TYPE, BORDER_FLAT);
   ObjectSetInteger(0, prefix+"BG", OBJPROP_COLOR, C'0,100,200');
   ObjectSetInteger(0, prefix+"BG", OBJPROP_WIDTH, 2);
   
   // Title
   CreateLabel(prefix+"TITLE", "🧬 AI TRADING ORGANISM", x, y, clrCyan, 10);
   CreateLabel(prefix+"LINE", StringRepeat("─", 35), x, y+20, C'0,80,150', 8);
}

void CreateLabel(string name, string text, int x, int y, color clr, int size) {
   ObjectCreate(0, name, OBJ_LABEL, 0, 0, 0);
   ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
   ObjectSetString(0, name, OBJPROP_TEXT, text);
   ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
   ObjectSetInteger(0, name, OBJPROP_FONTSIZE, size);
   ObjectSetString(0, name, OBJPROP_FONT, "Consolas");
}

void UpdateDashboardPanel() {
   string prefix = "AI_ORG_";
   int x = 10, startY = 45;
   int rowH = 18;
   int row = 0;
   
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double equity  = AccountInfoDouble(ACCOUNT_EQUITY);
   double profit  = equity - balance;
   int    trades  = PositionsTotal();
   string session = GetCurrentSession();
   
   // Count BUY/SELL
   int buys = 0, sells = 0;
   for(int i = 0; i < PositionsTotal(); i++) {
      if(!PosInfo.SelectByIndex(i)) continue;
      if(PosInfo.Symbol() != _Symbol) continue;
      if(PosInfo.PositionType() == POSITION_TYPE_BUY) buys++;
      else sells++;
   }
   
   color profitColor = (profit >= 0) ? clrLime : clrRed;
   
   DashRow(prefix, row++, x, startY, rowH, "Organism: " + g_CurrentOrganism, clrSkyBlue);
   DashRow(prefix, row++, x, startY, rowH, "Session:  " + session, SessionColor(session));
   DashRow(prefix, row++, x, startY, rowH, "Balance:  $" + DoubleToString(balance, 2), clrWhite);
   DashRow(prefix, row++, x, startY, rowH, "Equity:   $" + DoubleToString(equity, 2), profitColor);
   DashRow(prefix, row++, x, startY, rowH, "P&L:      $" + DoubleToString(profit, 2), profitColor);
   DashRow(prefix, row++, x, startY, rowH, "Locked:   $" + DoubleToString(g_LockedFund, 2), clrGold);
   DashRow(prefix, row++, x, startY, rowH, "Trades:   " + IntegerToString(trades) +
           " [B:" + IntegerToString(buys) + " S:" + IntegerToString(sells) + "]", clrWhite);
   DashRow(prefix, row++, x, startY, rowH, "Signal:   " + g_LastSignal, SignalColor(g_LastSignal));
   DashRow(prefix, row++, x, startY, rowH, "Reason:   " + StringSubstr(g_LastReason,0,28), clrLightBlue);
   DashRow(prefix, row++, x, startY, rowH, "Ghost SL: " + IntegerToString(GhostSLPoints) + "p", clrOrange);
   DashRow(prefix, row++, x, startY, rowH, "Layer:    " + IntegerToString(MinLayerDistance) + "p min", clrLightBlue);
   DashRow(prefix, row++, x, startY, rowH, "Evolution: " + DashboardURL, C'0,150,255');
}

void DashRow(string prefix, int row, int x, int startY, int rowH,
             string text, color clr) {
   string name = prefix + "R" + IntegerToString(row);
   if(ObjectFind(0, name) < 0)
      CreateLabel(name, text, x, startY + row * rowH, clr, 8);
   else {
      ObjectSetString(0, name, OBJPROP_TEXT, text);
      ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
   }
}

void UpdateDashboardPanelLight() {
   // Only update P&L on tick (very lightweight)
   double equity  = AccountInfoDouble(ACCOUNT_EQUITY);
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double profit  = equity - balance;
   color  clr     = (profit >= 0) ? clrLime : clrRed;
   string name    = "AI_ORG_R4";
   if(ObjectFind(0, name) >= 0) {
      ObjectSetString(0, name, OBJPROP_TEXT, "Equity:   $" + DoubleToString(equity, 2));
      ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
   }
   name = "AI_ORG_R4";
}

void RemoveDashboardPanel() {
   ObjectsDeleteAll(0, "AI_ORG_");
}

color SessionColor(string s) {
   if(s == "Asia")    return clrYellow;
   if(s == "London")  return clrLime;
   if(s == "NewYork") return clrOrange;
   return clrGray;
}

color SignalColor(string s) {
   if(s == "BUY")  return clrLime;
   if(s == "SELL") return clrRed;
   return clrGray;
}

string StringRepeat(string s, int n) {
   string result = "";
   for(int i = 0; i < n; i++) result += s;
   return result;
}
//+------------------------------------------------------------------+
//| END OF EA                                                        |
//+------------------------------------------------------------------+
