#property strict

#include <Trade/Trade.mqh>

CTrade trade;

input double LotSize = 0.01;
input int Magic = 777;

string ReadSignal()
{
   int file=FileOpen("signal.json",FILE_READ|FILE_TXT|FILE_COMMON);

   if(file==INVALID_HANDLE)
      return "NONE";

   string text=FileReadString(file);
   FileClose(file);

   if(StringFind(text,"BUY")>=0)
      return "BUY";

   if(StringFind(text,"SELL")>=0)
      return "SELL";

   return "NONE";
}

bool PositionExists()
{
   for(int i=0;i<PositionsTotal();i++)
   {
      if(PositionGetSymbol(i)==Symbol())
         return true;
   }

   return false;
}

void OnTick()
{
   static datetime lastCandle=0;

   datetime candle=iTime(Symbol(),PERIOD_M1,0);

   if(candle==lastCandle)
      return;

   lastCandle=candle;

   string signal=ReadSignal();

   if(signal=="BUY" && !PositionExists())
      trade.Buy(LotSize,Symbol());

   if(signal=="SELL" && !PositionExists())
      trade.Sell(LotSize,Symbol());
}
