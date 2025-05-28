'use client';

import { useEffect, useState, useRef, useMemo, useCallback } from 'react';
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
import { ChevronDown, ChevronRight } from "lucide-react";
import { Toaster } from "sonner";
import React from 'react';

interface latest_main_coins_data {
  id: number;
  created_at: string;
  symbol: string;
  slug: string;
  name: string;
  ucid: number;
  price_usd: number | null;
  percent_change_1h: number | null;
  percent_change_24h: number | null;
  percent_change_7d: number | null;
  volume_24h: number | null;
  volume_change_24h: number | null;
  market_cap: number | null;
  market_cap_dominance: number | null;
  last_updated: string;
}

interface latest_meme_coins_data {
  id: number;
  token_symbol: string;
  token_name: string;
  chain_id: string;
  token_address: string;
  dex_id: string;
  pair_address: string | null;
  price_usd: number | null;
  price_native: number | null;
  percent_change_5m: number | null;
  percent_change_1h: number | null;
  percent_change_6h: number | null;
  percent_change_24h: number | null;
  txns_buys_5m: number | null;
  txns_sells_5m: number | null;
  txns_buys_1h: number | null;
  txns_sells_1h: number | null;
  txns_buys_6h: number | null;
  txns_sells_6h: number | null;
  txns_buys_24h: number | null;
  txns_sells_24h: number | null;
  volume_5m: number | null;
  volume_1h: number | null;
  volume_6h: number | null;
  volume_24h: number | null;
  liquidity_usd: number | null;
  liquidity_base: number | null;
  liquidity_quote: number | null;
  last_updated: string;
  is_active: boolean;
  market_cap: number | null;
}

interface DexPairInfo {
  dex_id: string;
  pair_address: string;
}

interface token_info {
  id: number;
  chain_id: string;
  token_address: string;
  token_name: string;
  token_symbol: string;
  token_icon_url: string | null;
  token_websites: string[] | null;
  token_socials: string[] | null;
  quote_token_address: string | null;
  quote_token_name: string | null;
  quote_token_symbol: string | null;
  dex_pairs: DexPairInfo[] | null;
}

interface ProcessedMemeToken {
  tokenInfo: token_info;
  allPairData: latest_meme_coins_data[];
  selectedPairData: latest_meme_coins_data;
}

type ChainType = 'main' | 'solana' | 'bsc' | 'base';

interface TokenDataState {
  mainCoins: latest_main_coins_data[];
  processedMemeTokensByChain: {
    solana: ProcessedMemeToken[];
    bsc: ProcessedMemeToken[];
    base: ProcessedMemeToken[];
  };
  rawTokenInfos: token_info[];
  rawMemeCoinPairs: latest_meme_coins_data[];
}

// 添加排序状态类型
type SortDirection = 'asc' | 'desc' | null;
type SortColumn = string | null;

// 修改 SupabaseRealtimePayload 类型
type SupabaseRealtimePayload<T> = {
  eventType: 'INSERT' | 'UPDATE' | 'DELETE';
  new: T;
  old: T;
  schema: string;
  table: string;
};

// 通用增量更新工具
function updateOrAdd<T>(arr: T[], newItem: T, idField: keyof T): T[] {
  let found = false;
  const newList = arr.map(item => {
    if (item[idField] === newItem[idField]) {
      found = true;
      return newItem;
    }
    return item;
  });
  if (!found) newList.push(newItem);
  return newList;
}

// 类型守卫，判断 err 是否有 message 字段
function isErrorWithMessage(e: unknown): e is { message: string } {
  return (
    typeof e === 'object' &&
    e !== null &&
    'message' in e &&
    typeof (e as { message?: unknown }).message === 'string'
  );
}

export default function DashboardPage() {
  const [tokenData, setTokenData] = useState<TokenDataState>({
    mainCoins: [],
    processedMemeTokensByChain: {
      solana: [],
      bsc: [],
      base: []
    },
    rawTokenInfos: [],
    rawMemeCoinPairs: []
  });
  const [error, setError] = useState<string | null>(null);
  const [lastUpdatedAt, setLastUpdatedAt] = useState<string | null>(null);
  const [selectedChain, setSelectedChain] = useState<ChainType>('main');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [expandedTokenPairs, setExpandedTokenPairs] = useState<{ [key: string]: boolean }>({});
  const [memePage, setMemePage] = useState(1);
  const memePageSize = 30;
  const memeTableRef = useRef<HTMLDivElement>(null);
  const [mainPage, setMainPage] = useState(1);
  const mainPageSize = 30;
  const mainTableRef = useRef<HTMLDivElement>(null);
  const [sortColumn, setSortColumn] = useState<SortColumn>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>(null);

  const formatUTCDate = (date: Date) => {
    const year = date.getUTCFullYear();
    const month = String(date.getUTCMonth() + 1).padStart(2, '0');
    const day = String(date.getUTCDate()).padStart(2, '0');
    const hours = String(date.getUTCHours()).padStart(2, '0');
    const minutes = String(date.getUTCMinutes()).padStart(2, '0');
    const seconds = String(date.getUTCSeconds()).padStart(2, '0');
    
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds} (UTC+0)`;
  };

  const processAndSetTokenData = (
    rawInfos: token_info[],
    rawPairs: latest_meme_coins_data[],
    mainCoinsData: latest_main_coins_data[]
  ) => {
    const newProcessedMemeTokensByChain: TokenDataState['processedMemeTokensByChain'] = {
      solana: [],
      bsc: [],
      base: []
    };
    rawInfos.forEach(info => {
      if (!info.dex_pairs || info.dex_pairs.length === 0) return;
      const relevantPairs = rawPairs.filter(pairData =>
        info.dex_pairs!.some(dp => dp.pair_address === pairData.pair_address && pairData.chain_id === info.chain_id)
      );
      if (relevantPairs.length === 0) return;
      const selectedPair = relevantPairs.reduce((max, pair) =>
        (pair.liquidity_usd || 0) > (max.liquidity_usd || 0) ? pair : max,
        relevantPairs[0]
      );
      const processedToken: ProcessedMemeToken = {
        tokenInfo: info,
        allPairData: relevantPairs,
        selectedPairData: selectedPair
      };
      if (info.chain_id === 'solana') newProcessedMemeTokensByChain.solana.push(processedToken);
      else if (info.chain_id === 'bsc') newProcessedMemeTokensByChain.bsc.push(processedToken);
      else if (info.chain_id === 'base') newProcessedMemeTokensByChain.base.push(processedToken);
    });
    setTokenData(prevState => ({
      ...prevState,
      mainCoins: mainCoinsData,
      processedMemeTokensByChain: newProcessedMemeTokensByChain,
      rawTokenInfos: rawInfos,
      rawMemeCoinPairs: rawPairs,
    }));
  };

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [mainCoinsResponse, memePairsResponse, tokenInfosResponse] = await Promise.all([
        supabase.from('latest_main_coins_data').select('*'),
        supabase.from('latest_meme_coins_data').select('*'),
        supabase.from('token_info').select('*')
      ]);

      if (mainCoinsResponse.error) throw mainCoinsResponse.error;
      if (memePairsResponse.error) throw memePairsResponse.error;
      if (tokenInfosResponse.error) throw tokenInfosResponse.error;

      const mainCoinsData = mainCoinsResponse.data as latest_main_coins_data[];
      const rawPairsData = memePairsResponse.data as latest_meme_coins_data[];
      const rawInfosData = tokenInfosResponse.data as token_info[];
      
      processAndSetTokenData(rawInfosData, rawPairsData, mainCoinsData);

      const lastUpdatedTimes = [
        ...mainCoinsData.map(d => d.last_updated),
        ...rawPairsData.map(d => d.last_updated),
      ].filter(Boolean).map(d => new Date(d).getTime());

      if (lastUpdatedTimes.length > 0) {
        setLastUpdatedAt(formatUTCDate(new Date(Math.max(...lastUpdatedTimes))));
      } else {
        setLastUpdatedAt(formatUTCDate(new Date()));
      }

    } catch (err: unknown) {
      let message = 'Unknown error';
      if (isErrorWithMessage(err)) {
        message = err.message;
      } else if (typeof err === 'string') {
        message = err;
      } else {
        try {
          message = JSON.stringify(err);
        } catch {
          // ignore
        }
      }
      console.error('Error fetching data:', err, message);
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const updateTokenData = useCallback((
    payload: SupabaseRealtimePayload<latest_main_coins_data | latest_meme_coins_data | token_info>,
    type: 'main' | 'meme_pair' | 'token_info'
  ) => {
    setTokenData(prevData => {
      let newRawTokenInfos = prevData.rawTokenInfos;
      let newRawMemeCoinPairs = prevData.rawMemeCoinPairs;
      let newMainCoins = prevData.mainCoins;
      let newProcessedMemeTokensByChain = prevData.processedMemeTokensByChain;

      if (type === 'main') {
        const mainPayload = payload as SupabaseRealtimePayload<latest_main_coins_data>;
        if (payload.eventType === 'DELETE') {
          newMainCoins = prevData.mainCoins.filter(t => t.id !== mainPayload.old.id);
        } else {
          newMainCoins = updateOrAdd(prevData.mainCoins, mainPayload.new, 'id');
        }
      } else if (type === 'token_info') {
        const tokenInfoPayload = payload as SupabaseRealtimePayload<token_info>;
        if (payload.eventType === 'DELETE') {
          newRawTokenInfos = prevData.rawTokenInfos.filter(t => t.id !== tokenInfoPayload.old.id);
          const chain = tokenInfoPayload.old.chain_id as 'solana' | 'bsc' | 'base';
          newProcessedMemeTokensByChain = {
            ...prevData.processedMemeTokensByChain,
            [chain]: prevData.processedMemeTokensByChain[chain].filter(t => t.tokenInfo.token_address !== tokenInfoPayload.old.token_address)
          };
        } else {
          newRawTokenInfos = updateOrAdd(prevData.rawTokenInfos, tokenInfoPayload.new, 'id');
          newProcessedMemeTokensByChain = updateProcessedMemeTokensByChain(
            prevData.processedMemeTokensByChain,
            tokenInfoPayload.new,
            prevData.rawMemeCoinPairs
          );
        }
      } else if (type === 'meme_pair') {
        const memePairPayload = payload as SupabaseRealtimePayload<latest_meme_coins_data>;
        if (payload.eventType === 'DELETE') {
          newRawMemeCoinPairs = prevData.rawMemeCoinPairs.filter(p => p.pair_address !== memePairPayload.old.pair_address);
          prevData.rawTokenInfos.forEach(info => {
            if (info.dex_pairs?.some(dp => dp.pair_address === memePairPayload.old.pair_address)) {
              newProcessedMemeTokensByChain = updateProcessedMemeTokensByChain(
                newProcessedMemeTokensByChain,
                info,
                newRawMemeCoinPairs
              );
            }
          });
        } else {
          newRawMemeCoinPairs = updateOrAdd(prevData.rawMemeCoinPairs, memePairPayload.new, 'pair_address');
          prevData.rawTokenInfos.forEach(info => {
            if (info.dex_pairs?.some(dp => dp.pair_address === memePairPayload.new.pair_address)) {
              newProcessedMemeTokensByChain = updateProcessedMemeTokensByChain(
                newProcessedMemeTokensByChain,
                info,
                newRawMemeCoinPairs
              );
            }
          });
        }
      }
      return {
        ...prevData,
        mainCoins: newMainCoins,
        processedMemeTokensByChain: newProcessedMemeTokensByChain,
        rawTokenInfos: newRawTokenInfos,
        rawMemeCoinPairs: newRawMemeCoinPairs,
      };
    });
    setLastUpdatedAt(formatUTCDate(new Date()));
  }, []);

  useEffect(() => {
    let mainCoinsChannel: ReturnType<typeof supabase.channel> | null = null;
    let memePairsChannel: ReturnType<typeof supabase.channel> | null = null;
    let tokenInfoChannel: ReturnType<typeof supabase.channel> | null = null;

    const setupChannels = () => {
      if (mainCoinsChannel) supabase.removeChannel(mainCoinsChannel);
      if (memePairsChannel) supabase.removeChannel(memePairsChannel);
      if (tokenInfoChannel) supabase.removeChannel(tokenInfoChannel);

      mainCoinsChannel = supabase.channel('latest_main_coins_data_changes')
        .on('postgres_changes', { event: '*', schema: 'public', table: 'latest_main_coins_data' },
          (payload) => { 
            const typedPayload = payload as unknown as SupabaseRealtimePayload<latest_main_coins_data>;
            updateTokenData(typedPayload, 'main'); 
          })
        .subscribe();

      memePairsChannel = supabase.channel('latest_meme_coins_data_changes')
        .on('postgres_changes', { event: '*', schema: 'public', table: 'latest_meme_coins_data' },
          (payload) => { 
            const typedPayload = payload as unknown as SupabaseRealtimePayload<latest_meme_coins_data>;
            updateTokenData(typedPayload, 'meme_pair'); 
          })
        .subscribe();
      
      tokenInfoChannel = supabase.channel('token_info_changes')
        .on('postgres_changes', { event: '*', schema: 'public', table: 'token_info' },
          (payload) => { 
            const typedPayload = payload as unknown as SupabaseRealtimePayload<token_info>;
            updateTokenData(typedPayload, 'token_info'); 
          })
        .subscribe();
    };

    fetchData();
    setupChannels();

    return () => {
      if (mainCoinsChannel) supabase.removeChannel(mainCoinsChannel);
      if (memePairsChannel) supabase.removeChannel(memePairsChannel);
      if (tokenInfoChannel) supabase.removeChannel(tokenInfoChannel);
    };
  }, [fetchData, updateTokenData]);

  useEffect(() => {
    let el: HTMLDivElement | null = null;
    let handleScroll: (() => void) | null = null;
    if (selectedChain === 'main') {
      handleScroll = () => {
        el = mainTableRef.current;
        if (!el) return;
        if (el.scrollHeight - el.scrollTop - el.clientHeight < 100) {
          setMainPage(page => page + 1);
        }
      };
      el = mainTableRef.current;
    } else {
      handleScroll = () => {
        el = memeTableRef.current;
        if (!el) return;
        if (el.scrollHeight - el.scrollTop - el.clientHeight < 100) {
          setMemePage(page => page + 1);
        }
      };
      el = memeTableRef.current;
    }
    if (el && handleScroll) el.addEventListener('scroll', handleScroll);
    return () => { if (el && handleScroll) el.removeEventListener('scroll', handleScroll); };
  }, [selectedChain]);

  useEffect(() => { setMemePage(1); setMainPage(1); }, [selectedChain]);

  // 修改排序处理函数
  const handleSort = (column: string) => {
    if (sortColumn === column) {
      if (sortDirection === 'desc') {
        setSortDirection('asc');
      } else if (sortDirection === 'asc') {
        setSortColumn(null);
        setSortDirection(null);
      } else {
        setSortDirection('desc');
      }
    } else {
      setSortColumn(column);
      setSortDirection('desc');
    }
  };

  // 修改排序逻辑
  const mainCoinsSorted = useMemo(() => {
    const sorted = [...tokenData.mainCoins];
    if (sortColumn && sortDirection) {
      sorted.sort((a, b) => {
        const aValue = a[sortColumn as keyof latest_main_coins_data];
        const bValue = b[sortColumn as keyof latest_main_coins_data];
        
        if (aValue === null && bValue === null) return 0;
        if (aValue === null) return sortDirection === 'asc' ? -1 : 1;
        if (bValue === null) return sortDirection === 'asc' ? 1 : -1;
        
        if (typeof aValue === 'number' && typeof bValue === 'number') {
          return sortDirection === 'asc' ? aValue - bValue : bValue - aValue;
        }
        
        return 0;
      });
    } else {
      // 默认按 id 升序排序
      sorted.sort((a, b) => a.id - b.id);
    }
    return sorted;
  }, [tokenData.mainCoins, sortColumn, sortDirection]);

  const memeCoinsPaged = useMemo(() => {
    let all = tokenData.processedMemeTokensByChain[selectedChain as 'solana' | 'bsc' | 'base'] || [];
    
    if (sortColumn && sortDirection) {
      all = [...all].sort((a, b) => {
        const aValue = a.selectedPairData[sortColumn as keyof latest_meme_coins_data];
        const bValue = b.selectedPairData[sortColumn as keyof latest_meme_coins_data];
        
        if (aValue === null && bValue === null) return 0;
        if (aValue === null) return sortDirection === 'asc' ? -1 : 1;
        if (bValue === null) return sortDirection === 'asc' ? 1 : -1;
        
        if (typeof aValue === 'number' && typeof bValue === 'number') {
          return sortDirection === 'asc' ? aValue - bValue : bValue - aValue;
        }
        
        return 0;
      });
    }
    
    return all.slice(0, memePage * memePageSize);
  }, [tokenData.processedMemeTokensByChain, selectedChain, memePage, memePageSize, sortColumn, sortDirection]);

  const mainCoinsPaged = useMemo(() => {
    return mainCoinsSorted.slice(0, mainPage * mainPageSize);
  }, [mainCoinsSorted, mainPage, mainPageSize]);

  const getCurrentData = (): (latest_main_coins_data | ProcessedMemeToken)[] => {
    if (selectedChain === 'main') {
      return mainCoinsPaged;
    } else {
      return memeCoinsPaged;
    }
  };
  
  const formatNumber = (value: number | null | undefined, options: Intl.NumberFormatOptions = {}) => {
    if (value == null) return 'N/A';
    return value.toLocaleString(undefined, options);
  };

  const formatPercentage = (value: number | null | undefined) => {
    if (value == null) return 'N/A';
    return `${value.toFixed(2)}%`;
  };

  const getChangeColor = (value: number | null | undefined) => {
    if (value == null) return '';
    return value > 0 ? 'text-[var(--positive-foreground)]' : value < 0 ? 'text-[var(--negative-foreground)]' : '';
  };

  const toggleTokenPairsExpansion = (tokenAddress: string) => {
    setExpandedTokenPairs(prev => ({
      ...prev,
      [tokenAddress]: !prev[tokenAddress]
    }));
  };

  // 增量更新工具函数
  function updateProcessedMemeTokensByChain(
    prev: TokenDataState['processedMemeTokensByChain'],
    updatedToken: token_info,
    allPairs: latest_meme_coins_data[],
  ) {
    const chain = updatedToken.chain_id as 'solana' | 'bsc' | 'base';
    const prevList = prev[chain] || [];
    // 找到所有相关pair
    const relevantPairs = allPairs.filter(pairData =>
      updatedToken.dex_pairs?.some(dp => dp.pair_address === pairData.pair_address && pairData.chain_id === updatedToken.chain_id)
    );
    if (relevantPairs.length === 0) return prev;
    const selectedPair = relevantPairs.reduce((max, pair) =>
      (pair.liquidity_usd || 0) > (max.liquidity_usd || 0) ? pair : max,
      relevantPairs[0]
    );
    const newToken: ProcessedMemeToken = {
      tokenInfo: updatedToken,
      allPairData: relevantPairs,
      selectedPairData: selectedPair
    };
    // 替换或插入该token
    let found = false;
    const newList = prevList.map(t => {
      if (t.tokenInfo.token_address === updatedToken.token_address) {
        found = true;
        return newToken;
      }
      return t;
    });
    if (!found) newList.push(newToken);
    return {
      ...prev,
      [chain]: newList
    };
  }

  // 添加排序指示器组件
  const SortIndicator = ({ column }: { column: string }) => {
    if (sortColumn !== column) return null;
    return (
      <span className="ml-1">
        {sortDirection === 'asc' ? '↑' : '↓'}
      </span>
    );
  };

  return (
    <div className="container py-5 mx-auto">
      <h1 className="text-3xl font-heading font-bold mb-2">Token Dashboard</h1>
      
      <div className="flex gap-2 mb-4">
        <Button
          variant={selectedChain === 'main' ? 'default' : 'outline'}
          onClick={() => setSelectedChain('main')}
          className="font-data"
          disabled={isLoading}
        >
          Main
        </Button>
        <Button
          variant={selectedChain === 'solana' ? 'default' : 'outline'}
          onClick={() => setSelectedChain('solana')}
          className="font-data"
          disabled={isLoading}
        >
          Solana
        </Button>
        <Button
          variant={selectedChain === 'bsc' ? 'default' : 'outline'}
          onClick={() => setSelectedChain('bsc')}
          className="font-data"
          disabled={isLoading}
        >
          BSC
        </Button>
        <Button
          variant={selectedChain === 'base' ? 'default' : 'outline'}
          onClick={() => setSelectedChain('base')}
          className="font-data"
          disabled={isLoading}
        >
          Base
        </Button>
      </div>

      {lastUpdatedAt && (
        <p className="text-xs text-muted-foreground mb-4 font-data">Last updated: {lastUpdatedAt}</p>
      )}

      {error && (
        <div className="p-4 mb-4 text-sm rounded-lg bg-[var(--destructive-background)] text-[var(--destructive-foreground)]" role="alert">
          <span className="font-medium">Error!</span> {error}
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center p-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      ) : getCurrentData().length === 0 && !error ? (
        <p>No tokens found...</p>
      ) : (
        <div ref={selectedChain === 'main' ? mainTableRef : memeTableRef} style={{ maxHeight: 700, overflowY: 'auto' }} className="overflow-x-auto rounded-md border w-full bg-card dark:bg-[var(--bg-surface)] dark:border-[var(--border-color)] shadow-[0_2px_8px_0_rgba(0,0,0,0.08)] dark:shadow-[0_2px_8px_0_rgba(255,255,255,0.08)] hover:shadow-[0_4px_12px_0_rgba(0,0,0,0.12)] dark:hover:shadow-[0_4px_12px_0_rgba(255,255,255,0.12)] transition-shadow duration-200">
          <Table>
            <TableHeader className="sticky top-0 bg-inherit z-10">
              <TableRow className="dark:border-[var(--border-color)]">
                {selectedChain === 'main' ? (
                  <>
                    <TableHead className="sticky left-0 bg-card dark:bg-[var(--bg-surface)] z-30 w-[200px] font-heading pl-4">Token</TableHead>
                    <TableHead 
                      className="bg-inherit dark:bg-[var(--bg-surface)] font-heading cursor-pointer hover:bg-muted/50"
                      onClick={() => handleSort('price_usd')}
                    >
                      Price <SortIndicator column="price_usd" />
                    </TableHead>
                    <TableHead 
                      className="bg-inherit dark:bg-[var(--bg-surface)] font-heading cursor-pointer hover:bg-muted/50"
                      onClick={() => handleSort('percent_change_1h')}
                    >
                      1h Change <SortIndicator column="percent_change_1h" />
                    </TableHead>
                    <TableHead 
                      className="bg-inherit dark:bg-[var(--bg-surface)] font-heading cursor-pointer hover:bg-muted/50"
                      onClick={() => handleSort('percent_change_24h')}
                    >
                      24h Change <SortIndicator column="percent_change_24h" />
                    </TableHead>
                    <TableHead 
                      className="bg-inherit dark:bg-[var(--bg-surface)] font-heading cursor-pointer hover:bg-muted/50"
                      onClick={() => handleSort('percent_change_7d')}
                    >
                      7d Change <SortIndicator column="percent_change_7d" />
                    </TableHead>
                    <TableHead 
                      className="bg-inherit dark:bg-[var(--bg-surface)] font-heading cursor-pointer hover:bg-muted/50"
                      onClick={() => handleSort('volume_24h')}
                    >
                      24h Volume <SortIndicator column="volume_24h" />
                    </TableHead>
                    <TableHead 
                      className="bg-inherit dark:bg-[var(--bg-surface)] font-heading cursor-pointer hover:bg-muted/50"
                      onClick={() => handleSort('market_cap')}
                    >
                      Market Cap <SortIndicator column="market_cap" />
                    </TableHead>
                    <TableHead 
                      className="bg-inherit dark:bg-[var(--bg-surface)] font-heading cursor-pointer hover:bg-muted/50"
                      onClick={() => handleSort('market_cap_dominance')}
                    >
                      Dominance <SortIndicator column="market_cap_dominance" />
                    </TableHead>
                  </>
                ) : (
                  <>
                    <TableHead className="sticky left-0 bg-card dark:bg-[var(--bg-surface)] z-30 w-[200px] font-heading pl-4">Token</TableHead>
                    <TableHead className="bg-inherit dark:bg-[var(--bg-surface)] font-heading">DEX</TableHead>
                    <TableHead 
                      className="bg-inherit dark:bg-[var(--bg-surface)] font-heading cursor-pointer hover:bg-muted/50"
                      onClick={() => handleSort('price_usd')}
                    >
                      Price <SortIndicator column="price_usd" />
                    </TableHead>
                    <TableHead 
                      className="bg-inherit dark:bg-[var(--bg-surface)] font-heading cursor-pointer hover:bg-muted/50"
                      onClick={() => handleSort('percent_change_5m')}
                    >
                      5m Change <SortIndicator column="percent_change_5m" />
                    </TableHead>
                    <TableHead 
                      className="bg-inherit dark:bg-[var(--bg-surface)] font-heading cursor-pointer hover:bg-muted/50"
                      onClick={() => handleSort('percent_change_1h')}
                    >
                      1h Change <SortIndicator column="percent_change_1h" />
                    </TableHead>
                    <TableHead 
                      className="bg-inherit dark:bg-[var(--bg-surface)] font-heading cursor-pointer hover:bg-muted/50"
                      onClick={() => handleSort('percent_change_6h')}
                    >
                      6h Change <SortIndicator column="percent_change_6h" />
                    </TableHead>
                    <TableHead 
                      className="bg-inherit dark:bg-[var(--bg-surface)] font-heading cursor-pointer hover:bg-muted/50"
                      onClick={() => handleSort('percent_change_24h')}
                    >
                      24h Change <SortIndicator column="percent_change_24h" />
                    </TableHead>
                    <TableHead 
                      className="bg-inherit dark:bg-[var(--bg-surface)] font-heading cursor-pointer hover:bg-muted/50"
                      onClick={() => handleSort('volume_5m')}
                    >
                      5m Volume <SortIndicator column="volume_5m" />
                    </TableHead>
                    <TableHead 
                      className="bg-inherit dark:bg-[var(--bg-surface)] font-heading cursor-pointer hover:bg-muted/50"
                      onClick={() => handleSort('volume_1h')}
                    >
                      1h Volume <SortIndicator column="volume_1h" />
                    </TableHead>
                    <TableHead 
                      className="bg-inherit dark:bg-[var(--bg-surface)] font-heading cursor-pointer hover:bg-muted/50"
                      onClick={() => handleSort('volume_6h')}
                    >
                      6h Volume <SortIndicator column="volume_6h" />
                    </TableHead>
                    <TableHead 
                      className="bg-inherit dark:bg-[var(--bg-surface)] font-heading cursor-pointer hover:bg-muted/50"
                      onClick={() => handleSort('volume_24h')}
                    >
                      24h Volume <SortIndicator column="volume_24h" />
                    </TableHead>
                    <TableHead 
                      className="bg-inherit dark:bg-[var(--bg-surface)] font-heading cursor-pointer hover:bg-muted/50"
                      onClick={() => handleSort('txns_buys_5m')}
                    >
                      5m Txns (B/S) <SortIndicator column="txns_buys_5m" />
                    </TableHead>
                    <TableHead 
                      className="bg-inherit dark:bg-[var(--bg-surface)] font-heading cursor-pointer hover:bg-muted/50"
                      onClick={() => handleSort('txns_buys_1h')}
                    >
                      1h Txns (B/S) <SortIndicator column="txns_buys_1h" />
                    </TableHead>
                    <TableHead 
                      className="bg-inherit dark:bg-[var(--bg-surface)] font-heading cursor-pointer hover:bg-muted/50"
                      onClick={() => handleSort('txns_buys_6h')}
                    >
                      6h Txns (B/S) <SortIndicator column="txns_buys_6h" />
                    </TableHead>
                    <TableHead 
                      className="bg-inherit dark:bg-[var(--bg-surface)] font-heading cursor-pointer hover:bg-muted/50"
                      onClick={() => handleSort('txns_buys_24h')}
                    >
                      24h Txns (B/S) <SortIndicator column="txns_buys_24h" />
                    </TableHead>
                    <TableHead 
                      className="bg-inherit dark:bg-[var(--bg-surface)] font-heading cursor-pointer hover:bg-muted/50"
                      onClick={() => handleSort('liquidity_usd')}
                    >
                      Liquidity <SortIndicator column="liquidity_usd" />
                    </TableHead>
                    <TableHead 
                      className="bg-inherit dark:bg-[var(--bg-surface)] font-heading cursor-pointer hover:bg-muted/50"
                      onClick={() => handleSort('market_cap')}
                    >
                      Market Cap <SortIndicator column="market_cap" />
                    </TableHead>
                  </>
                )}
              </TableRow>
            </TableHeader>
            <TableBody>
              {getCurrentData().map((item: latest_main_coins_data | ProcessedMemeToken) => {
                if (selectedChain === 'main') {
                  const token = item as latest_main_coins_data;
                  return (
                    <TableRow key={`main-${token.id}`} className="dark:border-[var(--border-color)]">
                      <TableCell className="sticky left-0 bg-card dark:bg-[var(--bg-surface)] z-30 pl-4">
                        <div className="flex items-center space-x-3 w-[200px]">
                          {token.ucid && (
                            <div className="w-7 h-7 rounded-full bg-muted dark:bg-muted flex-shrink-0 overflow-hidden">
                              <Image
                                src={`https://s2.coinmarketcap.com/static/img/coins/64x64/${token.ucid}.png`}
                                alt={`${token.name} icon`}
                                width={28}
                                height={28}
                                className="w-full h-full object-cover"
                                unoptimized
                              />
                            </div>
                          )}
                          <div className="flex flex-col items-start min-w-0 flex-1">
                            <a
                              href={`https://coinmarketcap.com/currencies/${token.slug}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="font-data font-bold truncate block hover:text-primary hover:underline transition-colors ml-1 max-w-[150px]"
                              title={token.name}
                            >
                              {token.name}
                            </a>
                            <span className="text-xs text-muted-foreground truncate block ml-1 max-w-[150px]">{token.symbol}</span>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell className="font-data">{formatNumber(token.price_usd, { style: 'currency', currency: 'USD', minimumFractionDigits: 2, maximumFractionDigits: 6 })}</TableCell>
                      <TableCell className={`font-data ${getChangeColor(token.percent_change_1h)}`}>{formatPercentage(token.percent_change_1h)}</TableCell>
                      <TableCell className={`font-data ${getChangeColor(token.percent_change_24h)}`}>{formatPercentage(token.percent_change_24h)}</TableCell>
                      <TableCell className={`font-data ${getChangeColor(token.percent_change_7d)}`}>{formatPercentage(token.percent_change_7d)}</TableCell>
                      <TableCell className="font-data">{formatNumber(token.volume_24h, {notation: 'compact', compactDisplay: 'short'})}</TableCell>
                      <TableCell className="font-data">{formatNumber(token.market_cap, { style: 'currency', currency: 'USD', notation: 'compact', compactDisplay: 'short' })}</TableCell>
                      <TableCell className="font-data">{formatPercentage(token.market_cap_dominance)}</TableCell>
                    </TableRow>
                  );
                } else {
                  const processedToken = item as ProcessedMemeToken;
                  const tokenInfo = processedToken.tokenInfo;
                  const selectedPair = processedToken.selectedPairData;
                  const isExpanded = expandedTokenPairs[tokenInfo.token_address] || false;

                  return (
                    <React.Fragment key={`meme-token-${tokenInfo.token_address}`}>
                      <TableRow key={`meme-${tokenInfo.token_address}-selected`} className="dark:border-[var(--border-color)] hover:bg-muted/50">
                        <TableCell className="sticky left-0 bg-card dark:bg-[var(--bg-surface)] z-30 pl-4">
                          <div className="flex items-center space-x-3 w-[200px]">
                            {tokenInfo.token_icon_url ? (
                              <div className="w-7 h-7 rounded-full bg-muted dark:bg-muted flex-shrink-0 overflow-hidden">
                                <Image src={tokenInfo.token_icon_url} alt={`${tokenInfo.token_name} icon`} width={28} height={28} className="w-full h-full object-cover" unoptimized/>
                              </div>
                            ) : (
                              <div className="w-7 h-7 rounded-full bg-muted dark:bg-muted flex-shrink-0" title={tokenInfo.token_name} />
                            )}
                            <div className="flex flex-col items-start min-w-0 flex-1">
                              <div className="flex items-center w-full">
                                <a href={`https://dexscreener.com/${selectedPair.chain_id}/${selectedPair.pair_address}`} target="_blank" rel="noopener noreferrer" className="font-data font-bold truncate block hover:text-primary hover:underline transition-colors ml-1" title={tokenInfo.token_name}>
                                  {tokenInfo.token_name}
                                </a>
                                {processedToken.allPairData.length > 1 && (
                                  <Button variant="ghost" size="icon" className="h-6 w-6 p-0.5 text-muted-foreground hover:text-foreground cursor-pointer ml-1 flex-shrink-0" onClick={() => toggleTokenPairsExpansion(tokenInfo.token_address)} title={isExpanded ? "Hide pairs" : "Show pairs"}>
                                    {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                                  </Button>
                                )}
                              </div>
                              <span className="text-xs text-muted-foreground truncate block ml-1">{tokenInfo.token_symbol}</span>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell className="font-data">{selectedPair.dex_id}</TableCell>
                        <TableCell className="font-data">{formatNumber(selectedPair.price_usd, { style: 'currency', currency: 'USD', minimumFractionDigits: 2, maximumFractionDigits: 8 })}</TableCell>
                        <TableCell className={`font-data ${getChangeColor(selectedPair.percent_change_5m)}`}>{formatPercentage(selectedPair.percent_change_5m)}</TableCell>
                        <TableCell className={`font-data ${getChangeColor(selectedPair.percent_change_1h)}`}>{formatPercentage(selectedPair.percent_change_1h)}</TableCell>
                        <TableCell className={`font-data ${getChangeColor(selectedPair.percent_change_6h)}`}>{formatPercentage(selectedPair.percent_change_6h)}</TableCell>
                        <TableCell className={`font-data ${getChangeColor(selectedPair.percent_change_24h)}`}>{formatPercentage(selectedPair.percent_change_24h)}</TableCell>
                        <TableCell className="font-data">{formatNumber(selectedPair.volume_5m, {notation: 'compact', compactDisplay: 'short'})}</TableCell>
                        <TableCell className="font-data">{formatNumber(selectedPair.volume_1h, {notation: 'compact', compactDisplay: 'short'})}</TableCell>
                        <TableCell className="font-data">{formatNumber(selectedPair.volume_6h, {notation: 'compact', compactDisplay: 'short'})}</TableCell>
                        <TableCell className="font-data">{formatNumber(selectedPair.volume_24h, {notation: 'compact', compactDisplay: 'short'})}</TableCell>
                        <TableCell className="font-data">{`${selectedPair.txns_buys_5m ?? 0}/${selectedPair.txns_sells_5m ?? 0}`}</TableCell>
                        <TableCell className="font-data">{`${selectedPair.txns_buys_1h ?? 0}/${selectedPair.txns_sells_1h ?? 0}`}</TableCell>
                        <TableCell className="font-data">{`${selectedPair.txns_buys_6h ?? 0}/${selectedPair.txns_sells_6h ?? 0}`}</TableCell>
                        <TableCell className="font-data">{`${selectedPair.txns_buys_24h ?? 0}/${selectedPair.txns_sells_24h ?? 0}`}</TableCell>
                        <TableCell className="font-data">{formatNumber(selectedPair.liquidity_usd, { style: 'currency', currency: 'USD', notation: 'compact', compactDisplay: 'short' })}</TableCell>
                        <TableCell className="font-data">{formatNumber(selectedPair.market_cap, { style: 'currency', currency: 'USD', notation: 'compact', compactDisplay: 'short' })}</TableCell>
                      </TableRow>
                      {isExpanded && processedToken.allPairData.filter(pairData => pairData.pair_address !== selectedPair.pair_address).map((pairData, index) => (
                        <TableRow key={`meme-${tokenInfo.token_address}-pair-${pairData.pair_address || index}`} className="dark:border-[var(--border-color)] bg-muted/20 hover:bg-muted/50">
                          <TableCell className="sticky left-0 bg-card dark:bg-[var(--bg-surface)] z-20 pl-16">
                            <div className="flex items-center space-x-3 w-[calc(200px-1.5rem)]">
                              <a href={`https://dexscreener.com/${pairData.chain_id}/${pairData.pair_address}`} target="_blank" rel="noopener noreferrer" className="font-data text-sm truncate block hover:text-primary hover:underline transition-colors" title={`View ${pairData.dex_id} pair on DexScreener`}>
                                {pairData.dex_id} Pair
                              </a>
                            </div>
                          </TableCell>
                          <TableCell className="font-data text-sm">{pairData.dex_id}</TableCell>
                          <TableCell className="font-data text-sm">{formatNumber(pairData.price_usd, { style: 'currency', currency: 'USD', minimumFractionDigits: 2, maximumFractionDigits: 8 })}</TableCell>
                          <TableCell className={`font-data text-sm ${getChangeColor(pairData.percent_change_5m)}`}>{formatPercentage(pairData.percent_change_5m)}</TableCell>
                          <TableCell className={`font-data text-sm ${getChangeColor(pairData.percent_change_1h)}`}>{formatPercentage(pairData.percent_change_1h)}</TableCell>
                          <TableCell className={`font-data text-sm ${getChangeColor(pairData.percent_change_6h)}`}>{formatPercentage(pairData.percent_change_6h)}</TableCell>
                          <TableCell className={`font-data text-sm ${getChangeColor(pairData.percent_change_24h)}`}>{formatPercentage(pairData.percent_change_24h)}</TableCell>
                          <TableCell className="font-data text-sm">{formatNumber(pairData.volume_5m, {notation: 'compact', compactDisplay: 'short'})}</TableCell>
                          <TableCell className="font-data text-sm">{formatNumber(pairData.volume_1h, {notation: 'compact', compactDisplay: 'short'})}</TableCell>
                          <TableCell className="font-data text-sm">{formatNumber(pairData.volume_6h, {notation: 'compact', compactDisplay: 'short'})}</TableCell>
                          <TableCell className="font-data text-sm">{formatNumber(pairData.volume_24h, {notation: 'compact', compactDisplay: 'short'})}</TableCell>
                          <TableCell className="font-data text-sm">{`${pairData.txns_buys_5m ?? 0}/${pairData.txns_sells_5m ?? 0}`}</TableCell>
                          <TableCell className="font-data text-sm">{`${pairData.txns_buys_1h ?? 0}/${pairData.txns_sells_1h ?? 0}`}</TableCell>
                          <TableCell className="font-data text-sm">{`${pairData.txns_buys_6h ?? 0}/${pairData.txns_sells_6h ?? 0}`}</TableCell>
                          <TableCell className="font-data text-sm">{`${pairData.txns_buys_24h ?? 0}/${pairData.txns_sells_24h ?? 0}`}</TableCell>
                          <TableCell className="font-data text-sm">{formatNumber(pairData.liquidity_usd, { style: 'currency', currency: 'USD', notation: 'compact', compactDisplay: 'short' })}</TableCell>
                          <TableCell className="font-data text-sm">{formatNumber(pairData.market_cap, { style: 'currency', currency: 'USD', notation: 'compact', compactDisplay: 'short' })}</TableCell>
                        </TableRow>
                      ))}
                    </React.Fragment>
                  );
                }
              })}
            </TableBody>
          </Table>
        </div>
      )}

      <Toaster richColors closeButton duration={1500} position="top-right" />
    </div>
  );
}