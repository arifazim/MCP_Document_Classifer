import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Box, 
  Typography, 
  Paper, 
  Button, 
  Grid, 
  Card, 
  CardContent, 
  Divider,
  Alert,
  CircularProgress,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Tab,
  Tabs
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import HistoryIcon from '@mui/icons-material/History';
import { fetchDocument, processDocument } from '../services/api';

function DocumentView() {
  const { documentId } = useParams();
  const navigate = useNavigate();
  const [document, setDocument] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [activeTab, setActiveTab] = useState(0);

  useEffect(() => {
    const loadDocument = async () => {
      try {
        const data = await fetchDocument(documentId, true);
        setDocument(data);
      } catch (err) {
        setError(`Error loading document: ${err.message || 'Unknown error'}`);
      } finally {
        setLoading(false);
      }
    };

    loadDocument();
  }, [documentId]);

  const handleProcessDocument = async () => {
    setProcessing(true);
    setError(null);
    
    try {
      const data = await processDocument(documentId);
      setDocument(data);
    } catch (err) {
      setError(`Processing failed: ${err.message || 'Unknown error'}`);
    } finally {
      setProcessing(false);
    }
  };

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.9) return 'success';
    if (confidence >= 0.7) return 'info';
    if (confidence >= 0.5) return 'warning';
    return 'error';
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 3 }}>
        {error}
      </Alert>
    );
  }

  if (!document) {
    return (
      <Alert severity="warning" sx={{ mb: 3 }}>
        Document not found
      </Alert>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          Document Details
        </Typography>
        <Button variant="outlined" onClick={() => navigate('/')}>
          Back to Dashboard
        </Button>
      </Box>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Typography variant="h6" gutterBottom>
              Document Information
            </Typography>
            <Typography variant="body1">
              <strong>Document ID:</strong> {document.document_id}
            </Typography>
            <Typography variant="body1">
              <strong>Filename:</strong> {document.metadata?.filename || 'N/A'}
            </Typography>
            <Typography variant="body1">
              <strong>Type:</strong> {document.metadata?.document_type || 'Unknown'}
            </Typography>
            <Typography variant="body1">
              <strong>Last Modified:</strong> {formatDate(document.metadata?.last_modified)}
            </Typography>
            <Typography variant="body1">
              <strong>File Size:</strong> {document.metadata?.file_size ? `${(document.metadata.file_size / 1024).toFixed(2)} KB` : 'N/A'}
            </Typography>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Typography variant="h6" gutterBottom>
              Processing Status
            </Typography>
            
            {document.processing_history && document.processing_history.length > 0 ? (
              <Box>
                <Chip 
                  label={document.processing_history[document.processing_history.length - 1]?.status || 'Unknown'} 
                  color={document.processing_history[document.processing_history.length - 1]?.status === 'completed' ? 'success' : 'default'} 
                  sx={{ mb: 2 }}
                />
                
                {document.metadata?.document_type ? (
                  <Typography variant="body1">
                    This document has been classified as a <strong>{document.metadata.document_type}</strong>.
                  </Typography>
                ) : (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="body1" color="text.secondary">
                      This document has not been processed yet.
                    </Typography>
                    <Button 
                      variant="contained" 
                      onClick={handleProcessDocument}
                      disabled={processing}
                      sx={{ mt: 1 }}
                    >
                      {processing ? 'Processing...' : 'Process Document'}
                    </Button>
                  </Box>
                )}
              </Box>
            ) : (
              <Box>
                <Typography variant="body1" color="text.secondary">
                  This document has not been processed yet.
                </Typography>
                <Button 
                  variant="contained" 
                  onClick={handleProcessDocument}
                  disabled={processing}
                  sx={{ mt: 1 }}
                >
                  {processing ? 'Processing...' : 'Process Document'}
                </Button>
              </Box>
            )}
          </Grid>
        </Grid>
      </Paper>

      <Box sx={{ mb: 3 }}>
        <Tabs value={activeTab} onChange={handleTabChange} aria-label="document tabs">
          <Tab label="Extracted Data" />
          <Tab label="Processing History" />
          <Tab label="Document Text" />
        </Tabs>
      </Box>

      {/* Extracted Data Tab */}
      {activeTab === 0 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Extracted Data
          </Typography>
          
          {Object.keys(document.extracted_data || {}).length === 0 ? (
            <Typography color="text.secondary">
              No data has been extracted from this document yet.
            </Typography>
          ) : (
            <Grid container spacing={2}>
              {Object.entries(document.extracted_data || {}).map(([key, value]) => {
                // Skip line_items for separate display
                if (key === 'line_items') return null;
                
                const confidence = document.confidence_scores?.[key] || 0;
                
                return (
                  <Grid item xs={12} sm={6} md={4} key={key}>
                    <Card variant="outlined">
                      <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                          <Typography variant="subtitle1" component="div" sx={{ textTransform: 'capitalize' }}>
                            {key.replace(/_/g, ' ')}
                          </Typography>
                          <Chip 
                            label={`${(confidence * 100).toFixed(0)}%`}
                            size="small"
                            color={getConfidenceColor(confidence)}
                          />
                        </Box>
                        <Typography variant="body1" sx={{ mt: 1, wordBreak: 'break-word' }}>
                          {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                );
              })}
            </Grid>
          )}
          
          {/* Line Items Section */}
          {document.extracted_data?.line_items && document.extracted_data.line_items.length > 0 && (
            <Box sx={{ mt: 4 }}>
              <Typography variant="h6" gutterBottom>
                Line Items
              </Typography>
              
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography>
                    {document.extracted_data.line_items.length} Line Items
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Box component="pre" sx={{ 
                    backgroundColor: '#f5f5f5', 
                    p: 2, 
                    borderRadius: 1,
                    overflow: 'auto',
                    maxHeight: 300
                  }}>
                    {JSON.stringify(document.extracted_data.line_items, null, 2)}
                  </Box>
                </AccordionDetails>
              </Accordion>
            </Box>
          )}
        </Paper>
      )}

      {/* Processing History Tab */}
      {activeTab === 1 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Processing History
          </Typography>
          
          {!document.processing_history || document.processing_history.length === 0 ? (
            <Typography color="text.secondary">
              No processing history available.
            </Typography>
          ) : (
            <List>
              {document.processing_history.map((entry, index) => (
                <React.Fragment key={index}>
                  <ListItem alignItems="flex-start">
                    <ListItemIcon>
                      <HistoryIcon />
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="subtitle1">
                            {entry.processor}
                          </Typography>
                          <Chip 
                            label={entry.status} 
                            size="small"
                            color={entry.status === 'completed' ? 'success' : entry.status === 'failed' ? 'error' : 'default'} 
                          />
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            {formatDate(entry.timestamp)}
                          </Typography>
                          {entry.details && Object.keys(entry.details).length > 0 && (
                            <Accordion sx={{ mt: 1 }}>
                              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                <Typography variant="body2">Details</Typography>
                              </AccordionSummary>
                              <AccordionDetails>
                                <Box component="pre" sx={{ 
                                  backgroundColor: '#f5f5f5', 
                                  p: 2, 
                                  borderRadius: 1,
                                  overflow: 'auto',
                                  fontSize: '0.8rem'
                                }}>
                                  {JSON.stringify(entry.details, null, 2)}
                                </Box>
                              </AccordionDetails>
                            </Accordion>
                          )}
                        </Box>
                      }
                    />
                  </ListItem>
                  {index < document.processing_history.length - 1 && <Divider variant="inset" component="li" />}
                </React.Fragment>
              ))}
            </List>
          )}
        </Paper>
      )}

      {/* Document Text Tab */}
      {activeTab === 2 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Document Text
          </Typography>
          
          {!document.text ? (
            <Typography color="text.secondary">
              Document text is not available. Try retrieving the document with the include_text parameter set to true.
            </Typography>
          ) : (
            <Box 
              sx={{ 
                backgroundColor: '#f5f5f5', 
                p: 3, 
                borderRadius: 1,
                whiteSpace: 'pre-wrap',
                overflow: 'auto',
                maxHeight: 500,
                fontFamily: 'monospace'
              }}
            >
              {document.text}
            </Box>
          )}
        </Paper>
      )}
    </Box>
  );
}

export default DocumentView;
