#property strict

#include <Trade/Trade.mqh>

CTrade trade;

input double Lot = 0.01;
input int LayerDistance = 50;

datetime lastCandle=0;

string ReadSignal()
{
   int file=FileOpen("signal.json",FILE_READ|FILE_TXT|FILE_COMMON);

   if(file==INVALID_HANDLE)
      return "WAIT";

   string txt=FileReadString(file);

   FileClose(file);

   if(StringFind(txt,"BUY")>=0) return "BUY";
   if(StringFind(txt,"SELL")>=0) return "SELL";

   return "WAIT";
}

bool PositionExists()
{
   for(int i=0;i<PositionsTotal();i++)
   {
      ulong ticket=PositionGetTicket(i);

      if(PositionSelectByTicket(ticket))
      {
         if(PositionGetString(POSITION_SYMBOL)==Symbol())
            return true;
      }
   }

   return false;
}

bool LayerAllowed()
{
   double last_price=0;

   for(int i=0;i<PositionsTotal();i++)
   {
      ulong ticket=PositionGetTicket(i);

      if(PositionSelectByTicket(ticket))
      {
         last_price=PositionGetDouble(POSITION_PRICE_OPEN);
      }
   }

   if(last_price==0) return true;

   if(MathAbs(SymbolInfoDouble(Symbol(),SYMBOL_BID)-last_price) > LayerDistance*_Point)
      return true;

   return false;
}

void OnTick()
{
   datetime candle=iTime(Symbol(),PERIOD_M1,0);

   if(candle==lastCandle) return;

   lastCandle=candle;

   string signal=ReadSignal();

   if(signal=="BUY" && LayerAllowed())
      trade.Buy(Lot);

   if(signal=="SELL" && LayerAllowed())
      trade.Sell(Lot);
}
