import axios from 'axios';
import React, { useState, useContext, useEffect, useCallback, useRef } from "react";

import AuthContext from '../../context/AuthContext';

import {   Loading_Spinner, PopUpComponent, Error_POP_Element } from "../../elements/main_elements";

// Импорт иконок для типов транзакций
import { ReactComponent as DepositIcon } from "../../media/svg/deposit.svg";
import { ReactComponent as WithdrawIcon } from "../../media/svg/withdraw.svg";
import { ReactComponent as PurchaseIcon } from "../../media/svg/purchase.svg";
import { ReactComponent as AddSlotsIcon } from "../../media/svg/add_slots.svg";
import { ReactComponent as RefundIcon } from "../../media/svg/refund.svg";
import { ReactComponent as RewardIcon } from "../../media/svg/reward.svg";
import { ReactComponent as WalletIcon } from "../../media/svg/wallet.svg";

function User_History_Title() {
    return (
      <div className="page_container">
        <div className="row_container">
            <h1 className="page_main_title_text">История транзакций</h1>
        </div>
      </div>
    );
}

function TransactionIcon({ type }) {
    const getIconAndClass = (type) => {
        switch (type) {
            case 'deposit':
                return { Icon: DepositIcon, className: 'deposit' };
            case 'withdraw':
                return { Icon: WithdrawIcon, className: 'withdraw' };
            case 'purchase_ready_task':
                return { Icon: PurchaseIcon, className: 'purchase_ready_task' };
            case 'purchase_slots':
                return { Icon: AddSlotsIcon, className: 'purchase_slots' };
            case 'refund':
                return { Icon: RefundIcon, className: 'refund' };
            case 'reward':
                return { Icon: RewardIcon, className: 'reward' };
            default:
                return { Icon: WalletIcon, className: 'default' };
        }
    };

    const { Icon, className } = getIconAndClass(type);

    return (
        <div className={`transaction-icon ${className}`}>
            <Icon />
        </div>
    );
}

function StatusBadge({ status }) {
    const getStatusText = (status) => {
        switch (status) {
            case 'pending':
                return 'В ожидании средств';
            case 'frozen':
                return 'Заморожены';
            case 'paid':
                return 'Исполнена';
            case 'canceled':
                return 'Отменен';
            case 'failed':
                return 'Ошибка';
            default:
                return status;
        }
    };

    const getStatusClass = (status) => {
        switch (status) {
            case 'pending':
                return 'pending';
            case 'frozen':
                return 'frozen';
            case 'paid':
                return 'paid';
            case 'canceled':
                return 'canceled';
            case 'failed':
                return 'failed';
            default:
                return 'default';
        }
    };

    return (
        <span className={`status-badge ${getStatusClass(status)}`}>
            {getStatusText(status)}
        </span>
    );
}

function TransactionTypeDisplay({ type }) {
    const getTypeDisplay = (type) => {
        switch (type) {
            case 'deposit':
                return 'Пополнение';
            case 'withdraw':
                return 'Вывод';
            case 'purchase_ready_task':
                return 'Покупка работы';
            case 'purchase_slots':
                return 'Покупка слотов';
            case 'refund':
                return 'Возврат';
            case 'reward':
                return 'Начисление за продажу';
            default:
                return type;
        }
    };

    return (
        <span className='transaction-type-text'>
            {getTypeDisplay(type)}
        </span>
    );
}

function User_History_Data_Element({ transaction }) {
    return (
        <div className='transaction-row'>
            {/* 1. Иконка с фоном */}
            <div className='transaction-icon-container'>
                <TransactionIcon type={transaction.type} />
            </div>
            
            {/* 2. Описание транзакции */}
            <div className='transaction-description'>
                <div className='transaction-amount'>
                    {transaction.formatted_amount}
                </div>
                <div className='transaction-date'>
                    {transaction.formatted_date}
                </div>
            </div>
            
            {/* 3. Надпись типа транзакции */}
            <div className='transaction-type'>
                <TransactionTypeDisplay type={transaction.type} />
            </div>
            
            {/* 4. Статус транзакции */}
            <div className='transaction-status-container'>
                <StatusBadge status={transaction.status} />
            </div>
            
            {/* 5. Дата транзакции */}
            <div className='transaction-date-container'>
                <div className='transaction-date-display'>
                    {transaction.formatted_date}
                </div>
            </div>
        </div>
    );
}

function User_History_Data({ transactions, loading, hasMore, onLoadMore, page }) {
    const observer = useRef();
    const lastTransactionRef = useCallback(node => {
        if (loading) return;
        if (observer.current) observer.current.disconnect();
        observer.current = new IntersectionObserver(entries => {
            if (entries[0].isIntersecting && hasMore) {
                onLoadMore();
            }
        });
        if (node) observer.current.observe(node);
    }, [loading, hasMore, onLoadMore]);

    return (
        <div className='page_container'>
            <div className='transactions_list'>
                {transactions.map((transaction, index) => {
                    if (transactions.length === index + 1) {
                        return (
                            <div key={transaction.id} ref={lastTransactionRef}>
                                <User_History_Data_Element transaction={transaction} />
                            </div>
                        );
                    } else {
                        return (
                            <User_History_Data_Element 
                                key={transaction.id} 
                                transaction={transaction} 
                            />
                        );
                    }
                })}
            </div>
            
            {transactions.length === 0 && !loading && (
                <div className='empty-transactions'>
                    <p>История транзакций пуста</p>
                </div>
            )}
            
            <div id="load-more-trigger" className="load-more-trigger"></div>
            {loading && page > 1 && <div className="loading-more">Загрузка...</div>}
        </div>
    );
}

function User_History() {
    const { accessToken } = useContext(AuthContext);
    const [transactions, setTransactions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [loadError, setLoadError] = useState(false);
    const [page, setPage] = useState(1);
    const [hasMore, setHasMore] = useState(true);
    const [loadingMore, setLoadingMore] = useState(false);

    const fetchTransactions = useCallback(async (pageNum = 1, append = false) => {
        try {
            const headers = accessToken ? { Authorization: `Bearer ${accessToken}` } : {};
            const response = await axios.get(`/api/payments/transactions/?page=${pageNum}&page_size=15`, { headers });
            
            const { transactions: newTransactions, has_next } = response.data;
            
            if (append) {
                setTransactions(prev => [...prev, ...newTransactions]);
            } else {
                setTransactions(newTransactions);
            }
            
            setHasMore(has_next);
            setLoadError(false);
        } catch (error) {
            console.error('Error fetching transactions:', error);
            setLoadError(true);
        } finally {
            setLoading(false);
            setLoadingMore(false);
        }
    }, [accessToken]);

    useEffect(() => {
        fetchTransactions(1, false);
    }, [fetchTransactions]);

    const handleLoadMore = () => {
        if (!loadingMore && hasMore) {
            setLoadingMore(true);
            const nextPage = page + 1;
            setPage(nextPage);
            fetchTransactions(nextPage, true);
        }
    };

    return (
        <div className="max_page_container">
            {loading && page === 1 && <Loading_Spinner />}
            {loadError && (
                <PopUpComponent
                    isVisible={loadError}
                    displayed={<Error_POP_Element />}
                    onClose={() => {
                        setLoadError(false);
                        window.history.back();
                    }}
                />
            )}
            <User_History_Title />
            <User_History_Data 
                transactions={transactions}
                loading={loadingMore}
                hasMore={hasMore}
                onLoadMore={handleLoadMore}
                page={page}
            />
        </div>
    );
}

export default User_History;