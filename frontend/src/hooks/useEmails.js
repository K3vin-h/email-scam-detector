import { useState, useEffect, useCallback } from 'react';
import { api } from '../api/client.js';

export function useEmails() {
  const [emails, setEmails] = useState([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [filter, setFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchEmails = useCallback(() => {
    setLoading(true);
    setError(null);
    const params = { page };
    if (filter !== '') params.is_scam = filter;
    api.getEmails(params)
      .then((data) => {
        setEmails(data.results);
        setCount(data.count);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [page, filter]);

  useEffect(() => { fetchEmails(); }, [fetchEmails]);

  const changeFilter = (newFilter) => {
    setPage(1);
    setFilter(newFilter);
  };

  return { emails, count, page, setPage, filter, changeFilter, loading, error, refetch: fetchEmails };
}
