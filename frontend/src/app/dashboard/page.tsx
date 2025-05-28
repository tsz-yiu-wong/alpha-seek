'use client';

import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import Image from 'next/image';
import { Button } from "@/components/ui/button";
import { Copy } from "lucide-react";
import { Toaster, toast } from "sonner";

// 警告：这是一个占位符 TokenData 接口。
// 您需要根据 'dex_solana_token_data' 表的实际列结构来更新此接口。
interface dex_token_data {
  id: number; // 主键
  created_at: string; // timestamptz
  token_address: string; // varchar
  pair_address: string | null; // varchar
  price_usd: number | null; // numeric
  price_native: number | null; // numeric
  price_change_5m: number | null; // numeric
  price_change_1h: number | null; // numeric
  price_change_6h: number | null; // numeric
  price_change_24h: number | null; // numeric
  txns_5m_buy: number | null; // int4
  txns_5m_sell: number | null; // int4
  txns_1h_buy: number | null; // int4
  txns_1h_sell: number | null; // int4
  txns_6h_buy: number | null; // int4
  txns_6h_sell: number | null; // int4
  txns_24h_buy: number | null; // int4
  txns_24h_sell: number | null; // int4
  volume_5m: number | null; // numeric
  volume_1h: number | null; // numeric
  volume_6h: number | null; // numeric
  volume_24h: number | null; // numeric
  liquidity_usd: number | null; // numeric
  liquidity_base: number | null; // int8
  liquidity_quote: number | null; // numeric
  market_cap: number | null; // numeric
}

// 新增：dex_solana_token_info 表的接口定义
// 假设的表结构，请根据实际情况调整
interface DexSolanaTokenInfo {
  pair_address: string; // 用于关联
  chain_id: string | null; // text
  dex_id: string | null; // text
  url: string | null; // varchar
  token_address: string | null; // varchar
  token_name: string | null; // varchar
  token_symbol: string | null; // varchar
  token_icon_url: string | null; // varchar
  token_websites: string | null; // jsonb
  token_socials: string | null; // jsonb
  quote_token_address: string | null; // varchar
  quote_token_name: string | null; // varchar
  quote_token_symbol: string | null; // varchar
}

// 新增：合并后的数据结构
interface CombinedTokenData extends dex_token_data {
  info?: DexSolanaTokenInfo | null; // 从 dex_solana_token_info 获取的信息
}

export default function DashboardPage() {
  const [tokens, setTokens] = useState<CombinedTokenData[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdatedAt, setLastUpdatedAt] = useState<string | null>(null);

  const handleCopy = async (text: string, tokenName?: string) => {
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      toast.success(`${tokenName ? tokenName + " address" : "Token address"} copied!`);
    } catch (err) {
      console.error('Failed to copy text: ', err);
      toast.error("Failed to copy address.");
    }
  };

  useEffect(() => {
    if (tokens.length > 0) {
      const mostRecentDate = tokens.reduce((max, token) => {
        const currentDate = new Date(token.created_at);
        return currentDate > max ? currentDate : max;
      }, new Date(0));

      if (mostRecentDate.getTime() !== new Date(0).getTime()) {
        const dateOptions: Intl.DateTimeFormatOptions = { year: 'numeric', month: '2-digit', day: '2-digit' };
        const timeOptions: Intl.DateTimeFormatOptions = { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false };

        const datePart = mostRecentDate.toLocaleDateString('en-GB', dateOptions);
        const timePart = mostRecentDate.toLocaleTimeString('en-GB', timeOptions);
        setLastUpdatedAt(`${datePart} ${timePart}`);
      }
    } else {
      setLastUpdatedAt(null);
    }
  }, [tokens]);

  useEffect(() => {
    const tokenDataTableName = 'dex_solana_token_data';
    const tokenInfoTableName = 'dex_solana_token_info';
    const channelName = `realtime-${tokenDataTableName}`;

    const fetchTokenInfo = async (pairAddress: string): Promise<DexSolanaTokenInfo | null> => {
      if (!pairAddress) return null;
      try {
        const { data, error } = await supabase
          .from(tokenInfoTableName)
          .select('*')
          .eq('pair_address', pairAddress)
          .maybeSingle();

        if (error) {
          console.warn(`Error fetching token info for ${pairAddress} from ${tokenInfoTableName}:`, error.message);
          return null;
        }
        return data as DexSolanaTokenInfo;
      } catch (e: any) {
        console.error(`Exception fetching token info for ${pairAddress}:`, e.message);
        return null;
      }
    };

    const fetchInitialData = async () => {
      setError(null);
      const { data: tokenDataList, error: tokenDataError } = await supabase
        .from(tokenDataTableName)
        .select('*');

      if (tokenDataError) {
        console.error('Error fetching initial data:', tokenDataError);
        setError(`Failed to load initial data from ${tokenDataTableName}: ${tokenDataError.message}`);
        setTokens([]);
        return;
      }

      if (tokenDataList) {
        const combinedDataPromises = (tokenDataList as dex_token_data[]).map(async (token) => {
          const info = token.pair_address ? await fetchTokenInfo(token.pair_address) : null;
          return { ...token, info: info || undefined };
        });
        const resolvedCombinedData = await Promise.all(combinedDataPromises);
        setTokens(resolvedCombinedData);
      } else {
        setTokens([]);
      }
    };

    fetchInitialData();

    const channel = supabase
      .channel(channelName)
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: tokenDataTableName },
        async (payload) => {
          console.log('Change received!', payload);
          
          let newRecord: dex_token_data | undefined;
          let oldRecordId: number | undefined;

          if (payload.eventType === 'INSERT' || payload.eventType === 'UPDATE') {
            newRecord = payload.new as dex_token_data;
          } else if (payload.eventType === 'DELETE') {
            const oldData = payload.old as Partial<dex_token_data> & { id?: number };
            if (oldData && typeof oldData.id === 'number') {
              oldRecordId = oldData.id;
            } else {
               console.warn('DELETE event received without old record ID. Full table refresh might be needed or check replica identity.');
               fetchInitialData();
               return;
            }
          }

          setTokens((prevTokens) => {
            let updatedTokens = [...prevTokens];

            if (payload.eventType === 'INSERT' && newRecord) {
              if (!prevTokens.find(t => t.id === (newRecord as dex_token_data).id)) {
                updatedTokens = [...prevTokens, { ...(newRecord as dex_token_data), info: undefined }];
                if (newRecord.pair_address) {
                    fetchTokenInfo(newRecord.pair_address).then(info => {
                        setTokens(currentTokens => currentTokens.map(t => t.id === (newRecord as dex_token_data).id ? {...t, info: info || undefined} : t));
                    });
                }
              }
            } else if (payload.eventType === 'UPDATE' && newRecord) {
              updatedTokens = prevTokens.map(token => {
                if (token.id === (newRecord as dex_token_data).id) {
                  const updatedToken = { ...token, ...(newRecord as dex_token_data) };
                   if (newRecord.pair_address && newRecord.pair_address !== token.pair_address) {
                        fetchTokenInfo(newRecord.pair_address).then(info => {
                            setTokens(currentTokens => currentTokens.map(t => t.id === (newRecord as dex_token_data).id ? {...t, info: info || undefined} : t));
                        });
                    } else if (newRecord.pair_address && !token.info) {
                        fetchTokenInfo(newRecord.pair_address).then(info => {
                            setTokens(currentTokens => currentTokens.map(t => t.id === (newRecord as dex_token_data).id ? {...t, info: info || undefined} : t));
                        });
                    }
                  return updatedToken;
                }
                return token;
              });
            } else if (payload.eventType === 'DELETE' && oldRecordId !== undefined) {
              updatedTokens = prevTokens.filter(token => token.id !== oldRecordId);
            }
            return updatedTokens;
          });
        }
      )
      .subscribe((status, err) => {
        if (err) {
          console.error('Subscription error:', err);
          setError(`Subscription to ${tokenDataTableName} failed: ${err ? err.message : 'Unknown error'}`);
        }
        console.log(`Supabase subscription status to ${tokenDataTableName}:`, status);
      });

    return () => {
      supabase.removeChannel(channel);
    };
  }, []);

  return (
    <div className="container py-5 mx-auto">
      <h1 className="text-3xl font-heading font-bold mb-2">Token Dashboard</h1>
      {lastUpdatedAt && (
        <p className="text-xs text-muted-foreground mb-4 font-data">Data updated at: {lastUpdatedAt}</p>
      )}
      
      {error && (
        <div className="p-4 mb-4 text-sm rounded-lg bg-[var(--destructive-background)] text-[var(--destructive-foreground)]" role="alert">
          <span className="font-medium">Error!</span> {error}
        </div>
      )}

      {tokens.length === 0 && !error && <p>Loading data or no tokens found...</p>}

      {tokens.length > 0 && (
        <div className="overflow-x-auto rounded-md border w-full 
                        bg-card dark:bg-[var(--bg-surface)]
                        dark:border-[var(--border-color)]
                        shadow-[0_2px_8px_0_rgba(0,0,0,0.08)]
                        dark:shadow-[0_2px_8px_0_rgba(255,255,255,0.08)]
                        hover:shadow-[0_4px_12px_0_rgba(0,0,0,0.12)]
                        dark:hover:shadow-[0_4px_12px_0_rgba(255,255,255,0.12)]
                        transition-shadow duration-200">
          <Table>
            <TableHeader className="sticky top-0 bg-inherit z-10">
              <TableRow className="dark:border-[var(--border-color)]">
                <TableHead className="sticky left-0 bg-card dark:bg-[var(--bg-surface)] z-10 w-[200px] font-heading">Token</TableHead>
                <TableHead className="bg-inherit dark:bg-[var(--bg-surface)] font-heading">Price</TableHead>
                <TableHead className="bg-inherit dark:bg-[var(--bg-surface)] font-heading">Price Change 5m</TableHead>
                <TableHead className="bg-inherit dark:bg-[var(--bg-surface)] font-heading">Price Change 1h</TableHead>
                <TableHead className="bg-inherit dark:bg-[var(--bg-surface)] font-heading">Price Change 6h</TableHead>
                <TableHead className="bg-inherit dark:bg-[var(--bg-surface)] font-heading">Price Change 24h</TableHead>
                <TableHead className="bg-inherit dark:bg-[var(--bg-surface)] font-heading">Volume 5m</TableHead>
                <TableHead className="bg-inherit dark:bg-[var(--bg-surface)] font-heading">Volume 1h</TableHead>
                <TableHead className="bg-inherit dark:bg-[var(--bg-surface)] font-heading">Volume 6h</TableHead>
                <TableHead className="bg-inherit dark:bg-[var(--bg-surface)] font-heading">Volume 24h</TableHead>
                <TableHead className="bg-inherit dark:bg-[var(--bg-surface)] font-heading">Txns 5m (B/S)</TableHead>
                <TableHead className="bg-inherit dark:bg-[var(--bg-surface)] font-heading">Txns 1h (B/S)</TableHead>
                <TableHead className="bg-inherit dark:bg-[var(--bg-surface)] font-heading">Txns 6h (B/S)</TableHead>
                <TableHead className="bg-inherit dark:bg-[var(--bg-surface)] font-heading">Txns 24h (B/S)</TableHead>
                <TableHead className="bg-inherit dark:bg-[var(--bg-surface)] font-heading">Liquidity USD</TableHead>
                <TableHead className="bg-inherit dark:bg-[var(--bg-surface)] font-heading">Market Cap</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {tokens.map((token) => (
                <TableRow key={token.id} className="dark:border-[var(--border-color)]">
                  <TableCell className="sticky left-0 bg-card dark:bg-[var(--bg-surface)] z-10">
                    <div className="flex items-center space-x-3 w-[200px]">
                      {token.info?.token_icon_url ? (
                        <Image 
                          src={token.info.token_icon_url} 
                          alt={token.info.token_name ?? token.info.token_symbol ?? 'token icon'} 
                          width={28}
                          height={28} 
                          className="rounded-full flex-shrink-0"
                          unoptimized
                        />
                      ) : (
                        <div 
                          className="w-7 h-7 rounded-full bg-muted dark:bg-muted flex-shrink-0"
                          title={token.info?.token_name ?? token.info?.token_symbol ?? 'token icon'}
                        />
                      )}
                      <div className="flex flex-col items-start min-w-0 flex-1">
                        <div className="flex items-center w-full">
                          <div className="flex-1 min-w-0 flex items-center">
                            {token.info?.token_address && (
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-6 w-6 p-0.5 text-muted-foreground hover:text-foreground cursor-pointer mr-0.5 flex-shrink-0"
                                onClick={() => handleCopy(token.info!.token_address!, (token.info?.token_name ?? token.info?.token_symbol) || undefined)}
                                title="Copy Token Address"
                              >
                                <Copy className="h-3.5 w-3.5" />
                              </Button>
                            )}
                            {token.info?.url ? (
                              <a 
                                href={token.info.url} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="font-data font-bold hover:underline text-[var(--link-foreground)] truncate block"
                                title={token.info.token_name ?? token.info.token_symbol ?? 'Unknown Token'}
                              >
                                {token.info.token_name ?? token.info.token_symbol ?? 'Unknown Token'}
                              </a>
                            ) : (
                              <span 
                                className="font-data font-bold truncate block"
                                title={token.info?.token_name ?? token.info?.token_symbol ?? 'Unknown Token'}
                              >
                                {token.info?.token_name ?? token.info?.token_symbol ?? 'Unknown Token'}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className="font-data">{token.price_usd?.toLocaleString(undefined, { style: 'currency', currency: 'USD', minimumFractionDigits: 2, maximumFractionDigits: 6 }) ?? 'N/A'}</TableCell>
                  <TableCell className={`font-data ${token.price_change_5m && token.price_change_5m > 0 ? 'text-[var(--positive-foreground)]' : token.price_change_5m && token.price_change_5m < 0 ? 'text-[var(--negative-foreground)]' : ''}`}>
                    {token.price_change_5m != null ? `${token.price_change_5m.toFixed(2)}%` : 'N/A'}
                  </TableCell>
                  <TableCell className={`font-data ${token.price_change_1h && token.price_change_1h > 0 ? 'text-[var(--positive-foreground)]' : token.price_change_1h && token.price_change_1h < 0 ? 'text-[var(--negative-foreground)]' : ''}`}>
                    {token.price_change_1h != null ? `${token.price_change_1h.toFixed(2)}%` : 'N/A'}
                  </TableCell>
                  <TableCell className={`font-data ${token.price_change_6h && token.price_change_6h > 0 ? 'text-[var(--positive-foreground)]' : token.price_change_6h && token.price_change_6h < 0 ? 'text-[var(--negative-foreground)]' : ''}`}>
                    {token.price_change_6h != null ? `${token.price_change_6h.toFixed(2)}%` : 'N/A'}
                  </TableCell>
                  <TableCell className={`font-data ${token.price_change_24h && token.price_change_24h > 0 ? 'text-[var(--positive-foreground)]' : token.price_change_24h && token.price_change_24h < 0 ? 'text-[var(--negative-foreground)]' : ''}`}>
                    {token.price_change_24h != null ? `${token.price_change_24h.toFixed(2)}%` : 'N/A'}
                  </TableCell>
                  <TableCell className="font-data">{token.volume_5m?.toLocaleString(undefined, {notation: 'compact', compactDisplay: 'short'}) ?? 'N/A'}</TableCell>
                  <TableCell className="font-data">{token.volume_1h?.toLocaleString(undefined, {notation: 'compact', compactDisplay: 'short'}) ?? 'N/A'}</TableCell>
                  <TableCell className="font-data">{token.volume_6h?.toLocaleString(undefined, {notation: 'compact', compactDisplay: 'short'}) ?? 'N/A'}</TableCell>
                  <TableCell className="font-data">{token.volume_24h?.toLocaleString(undefined, {notation: 'compact', compactDisplay: 'short'}) ?? 'N/A'}</TableCell>
                  <TableCell className="font-data">{`${token.txns_5m_buy ?? 0}/${token.txns_5m_sell ?? 0}`}</TableCell>
                  <TableCell className="font-data">{`${token.txns_1h_buy ?? 0}/${token.txns_1h_sell ?? 0}`}</TableCell>
                  <TableCell className="font-data">{`${token.txns_6h_buy ?? 0}/${token.txns_6h_sell ?? 0}`}</TableCell>
                  <TableCell className="font-data">{`${token.txns_24h_buy ?? 0}/${token.txns_24h_sell ?? 0}`}</TableCell>
                  <TableCell className="font-data">{token.liquidity_usd?.toLocaleString(undefined, { style: 'currency', currency: 'USD', notation: 'compact', compactDisplay: 'short' }) ?? 'N/A'}</TableCell>
                  <TableCell className="font-data">{token.market_cap?.toLocaleString(undefined, { style: 'currency', currency: 'USD', notation: 'compact', compactDisplay: 'short' }) ?? 'N/A'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      <Toaster richColors closeButton duration={1500} position="top-right" />
    </div>
  );
}