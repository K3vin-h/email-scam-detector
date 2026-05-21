import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../api/client.js';

export function useEmails() {
  const [emails, setEmails] = useState([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [filter, setFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const loadedRef = useRef(false);

  const fetchEmails = useCallback(() => {
    if (!loadedRef.current) setLoading(true);
    else setRefreshing(true);
    setError(null);
    const params = { page };
    if (filter !== '') params.risk_level = filter;
    api.getEmails(params)
      .then((data) => {
        setEmails(data.results);
        setCount(data.count);
      })
      .catch((err) => setError(err.message))
      .finally(() => {
        loadedRef.current = true;
        setLoading(false);
        setRefreshing(false);
      });
  }, [page, filter]);

  useEffect(() => { fetchEmails(); }, [fetchEmails]);

  const changeFilter = (newFilter) => {
    setPage(1);
    setFilter(newFilter);
  };

  const updateEmail = (gmailId, patch) => {
    setEmails((current) =>
      current.map((email) => email.gmail_id === gmailId ? { ...email, ...patch } : email)
    );
  };

  return { emails, count, page, setPage, filter, changeFilter, loading, refreshing, error, refetch: fetchEmails, updateEmail };
}
