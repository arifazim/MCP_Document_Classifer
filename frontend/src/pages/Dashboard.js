import React, { useState, useEffect } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { 
  Typography, 
  Grid, 
  Paper, 
  Box, 
  Card, 
  CardContent, 
  CardActions, 
  Button,
  Chip,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material';
import { Pie } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { fetchDocuments } from '../services/api';

// Register Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend);

function Dashboard() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    total: 0,
    byType: {
      invoice: 0,
      contract: 0,
      email: 0,
      unknown: 0
    }
  });

  useEffect(() => {
    const loadDocuments = async () => {
      try {
        const response = await fetchDocuments();
        // Extract documents array from the response
        const documentsArray = response.documents || [];
        setDocuments(documentsArray);
        
        // Calculate stats
        const newStats = {
          total: documentsArray.length,
          byType: {
            invoice: documentsArray.filter(doc => doc.document_type === 'invoice').length,
            contract: documentsArray.filter(doc => doc.document_type === 'contract').length,
            email: documentsArray.filter(doc => doc.document_type === 'email').length,
            unknown: documentsArray.filter(doc => !doc.document_type || doc.document_type === 'unknown').length
          }
        };
        setStats(newStats);
      } catch (error) {
        console.error('Error loading documents:', error);
        // Set empty array on error
        setDocuments([]);
      } finally {
        setLoading(false);
      }
    };

    loadDocuments();
  }, []);

  const chartData = {
    labels: ['Invoices', 'Contracts', 'Emails', 'Unknown'],
    datasets: [
      {
        data: [stats.byType.invoice, stats.byType.contract, stats.byType.email, stats.byType.unknown],
        backgroundColor: ['#4caf50', '#2196f3', '#ff9800', '#f44336'],
        hoverBackgroundColor: ['#388e3c', '#1976d2', '#f57c00', '#d32f2f'],
      },
    ],
  };

  const getStatusChip = (status) => {
    const statusColors = {
      uploaded: 'default',
      processed: 'success',
      failed: 'error',
      processing: 'warning'
    };
    
    return (
      <Chip 
        label={status} 
        color={statusColors[status] || 'default'} 
        size="small" 
      />
    );
  };

  const getDocumentTypeIcon = (type) => {
    const typeIcons = {
      invoice: '📄',
      contract: '📝',
      email: '📧',
      unknown: '❓'
    };
    
    return typeIcons[type] || typeIcons.unknown;
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} md={4}>
              <Paper sx={{ p: 2, height: '100%' }}>
                <Typography variant="h6" gutterBottom>
                  Document Statistics
                </Typography>
                <Box sx={{ height: 250, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                  <Pie data={chartData} options={{ maintainAspectRatio: false }} />
                </Box>
              </Paper>
            </Grid>
            
            <Grid item xs={12} md={8}>
              <Paper sx={{ p: 2, height: '100%' }}>
                <Typography variant="h6" gutterBottom>
                  Recent Documents
                </Typography>
                {documents.length === 0 ? (
                  <Box sx={{ textAlign: 'center', py: 4 }}>
                    <Typography color="textSecondary">
                      No documents found. Upload your first document to get started.
                    </Typography>
                    <Button 
                      component={RouterLink} 
                      to="/upload" 
                      variant="contained" 
                      sx={{ mt: 2 }}
                    >
                      Upload Document
                    </Button>
                  </Box>
                ) : (
                  <TableContainer>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>Type</TableCell>
                          <TableCell>Filename</TableCell>
                          <TableCell>Status</TableCell>
                          <TableCell>Actions</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {documents.slice(0, 5).map((doc) => (
                          <TableRow key={doc.document_id}>
                            <TableCell>
                              {getDocumentTypeIcon(doc.document_type)} {doc.document_type || 'Unknown'}
                            </TableCell>
                            <TableCell>{doc.filename}</TableCell>
                            <TableCell>{getStatusChip(doc.status)}</TableCell>
                            <TableCell>
                              <Button 
                                component={RouterLink} 
                                to={`/documents/${doc.document_id}`}
                                size="small"
                              >
                                View
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}
              </Paper>
            </Grid>
          </Grid>
          
          <Typography variant="h5" gutterBottom>
            All Documents
          </Typography>
          
          <Grid container spacing={3}>
            {documents.map((doc) => (
              <Grid item xs={12} sm={6} md={4} key={doc.document_id}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Typography variant="h6" component="div">
                        {getDocumentTypeIcon(doc.document_type)} {doc.document_type || 'Unknown'}
                      </Typography>
                      {getStatusChip(doc.status)}
                    </Box>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      {doc.filename}
                    </Typography>
                    <Typography variant="body2">
                      Uploaded: {new Date(doc.last_modified).toLocaleString()}
                    </Typography>
                  </CardContent>
                  <CardActions>
                    <Button 
                      component={RouterLink} 
                      to={`/documents/${doc.document_id}`}
                      size="small"
                    >
                      View Details
                    </Button>
                    {doc.status === 'uploaded' && (
                      <Button 
                        size="small" 
                        color="primary"
                      >
                        Process
                      </Button>
                    )}
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        </>
      )}
    </Box>
  );
}

export default Dashboard;
