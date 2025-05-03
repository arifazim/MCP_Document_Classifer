import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Typography, 
  Box, 
  Paper, 
  Button, 
  LinearProgress,
  Alert,
  Stepper,
  Step,
  StepLabel,
  Card,
  CardContent,
  CircularProgress
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { useDropzone } from 'react-dropzone';
import { uploadDocument, processDocument, checkMemoryStatus } from '../services/api';

const steps = ['Select Document', 'Upload Document', 'Process Document'];

function DocumentUpload() {
  const [activeStep, setActiveStep] = useState(0);
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [documentId, setDocumentId] = useState(null);
  const [error, setError] = useState(null);
  const [documentData, setDocumentData] = useState(null);
  const [debugInfo, setDebugInfo] = useState(null);
  const navigate = useNavigate();

  const onDrop = (acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
      setActiveStep(1);
      setError(null);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
      'text/plain': ['.txt'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
    },
    maxFiles: 1
  });

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError(null);
    
    try {
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 300);

      console.log('Uploading file:', file.name);
      const response = await uploadDocument(file);
      clearInterval(progressInterval);
      setUploadProgress(100);
      
      console.log('Upload response:', response);
      setDocumentId(response.document_id);
      setActiveStep(2);
      
      // Check memory status for debugging
      try {
        const memoryStatus = await checkMemoryStatus();
        console.log('Memory status after upload:', memoryStatus);
        setDebugInfo(prev => ({
          ...prev,
          memoryStatusAfterUpload: memoryStatus
        }));
      } catch (memoryError) {
        console.error('Error checking memory status:', memoryError);
      }
      
    } catch (err) {
      console.error('Upload error details:', err);
      setError(`Upload failed: ${err.message || 'Unknown error'}`);
    } finally {
      setUploading(false);
    }
  };

  const handleProcess = async () => {
    if (!documentId) {
      setError('No document ID available. Please upload a document first.');
      return;
    }

    setProcessing(true);
    setError(null);
    
    try {
      console.log('Processing document with ID:', documentId);
      
      // Check memory status before processing
      try {
        const memoryStatus = await checkMemoryStatus();
        console.log('Memory status before processing:', memoryStatus);
        setDebugInfo(prev => ({
          ...prev,
          memoryStatusBeforeProcessing: memoryStatus
        }));
      } catch (memoryError) {
        console.error('Error checking memory status:', memoryError);
      }
      
      const response = await processDocument(documentId);
      console.log('Process response:', response);
      setDocumentData(response);
      setActiveStep(3);
    } catch (err) {
      console.error('Processing error details:', err);
      setError(`Processing failed: ${err.message || 'Unknown error'}`);
    } finally {
      setProcessing(false);
    }
  };

  const handleViewDocument = () => {
    navigate(`/documents/${documentId}`);
  };

  const handleReset = () => {
    setActiveStep(0);
    setFile(null);
    setUploadProgress(0);
    setDocumentId(null);
    setDocumentData(null);
    setError(null);
    setDebugInfo(null);
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Upload Document
      </Typography>
      
      <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>
      
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}
      
      <Paper sx={{ p: 3, mb: 3 }}>
        {activeStep === 0 && (
          <Box>
            <Typography variant="h6" gutterBottom>
              Select a document to upload
            </Typography>
            <Box 
              {...getRootProps()} 
              sx={{
                border: '2px dashed #cccccc',
                borderRadius: 2,
                p: 5,
                textAlign: 'center',
                cursor: 'pointer',
                backgroundColor: isDragActive ? '#f0f8ff' : 'transparent',
                '&:hover': {
                  backgroundColor: '#f5f5f5'
                }
              }}
            >
              <input {...getInputProps()} />
              <CloudUploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
              {isDragActive ? (
                <Typography>Drop the document here...</Typography>
              ) : (
                <Typography>
                  Drag and drop a document here, or click to select a file
                </Typography>
              )}
              <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                Supported formats: PDF, JPG, PNG, TXT, DOCX
              </Typography>
            </Box>
          </Box>
        )}
        
        {activeStep === 1 && (
          <Box>
            <Typography variant="h6" gutterBottom>
              Upload Document
            </Typography>
            
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle1">
                Selected File: {file.name}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Size: {(file.size / 1024).toFixed(2)} KB
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Type: {file.type}
              </Typography>
            </Box>
            
            {uploading && (
              <Box sx={{ mb: 2 }}>
                <LinearProgress variant="determinate" value={uploadProgress} sx={{ mb: 1 }} />
                <Typography variant="body2" color="textSecondary">
                  Uploading... {uploadProgress}%
                </Typography>
              </Box>
            )}
            
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button 
                variant="outlined" 
                onClick={handleReset}
                disabled={uploading}
              >
                Change File
              </Button>
              <Button 
                variant="contained" 
                onClick={handleUpload}
                disabled={uploading}
              >
                {uploading ? <CircularProgress size={24} color="inherit" /> : 'Upload Document'}
              </Button>
            </Box>
          </Box>
        )}
        
        {activeStep === 2 && (
          <Box>
            <Typography variant="h6" gutterBottom>
              Process Document
            </Typography>
            
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <CheckCircleIcon color="success" sx={{ mr: 1 }} />
              <Typography>
                Document uploaded successfully! Document ID: {documentId}
              </Typography>
            </Box>
            
            <Typography variant="body1" paragraph>
              Your document has been uploaded. Now you can process it to extract information.
            </Typography>
            
            {processing && (
              <Box sx={{ mb: 2 }}>
                <LinearProgress sx={{ mb: 1 }} />
                <Typography variant="body2" color="textSecondary">
                  Processing document...
                </Typography>
              </Box>
            )}
            
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button 
                variant="outlined" 
                onClick={handleReset}
                disabled={processing}
              >
                Upload Another
              </Button>
              <Button 
                variant="contained" 
                onClick={handleProcess}
                disabled={processing}
              >
                {processing ? <CircularProgress size={24} color="inherit" /> : 'Process Document'}
              </Button>
            </Box>
            
            {/* Debug information */}
            {debugInfo && debugInfo.memoryStatusAfterUpload && (
              <Box sx={{ mt: 3 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Debug Information
                </Typography>
                <Card variant="outlined" sx={{ mt: 1 }}>
                  <CardContent>
                    <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap', fontSize: '0.75rem' }}>
                      {JSON.stringify(debugInfo.memoryStatusAfterUpload, null, 2)}
                    </Typography>
                  </CardContent>
                </Card>
              </Box>
            )}
          </Box>
        )}
        
        {activeStep === 3 && (
          <Box>
            <Typography variant="h6" gutterBottom>
              Processing Complete
            </Typography>
            
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <CheckCircleIcon color="success" sx={{ mr: 1 }} />
              <Typography>
                Document processed successfully!
              </Typography>
            </Box>
            
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="subtitle1" gutterBottom>
                  Document Type: {documentData?.document_type || 'Unknown'}
                </Typography>
                
                <Typography variant="subtitle2" gutterBottom>
                  Extracted Data:
                </Typography>
                
                <Box component="pre" sx={{ 
                  backgroundColor: '#f5f5f5', 
                  p: 2, 
                  borderRadius: 1,
                  overflow: 'auto',
                  maxHeight: 200
                }}>
                  {JSON.stringify(documentData?.extracted_data || {}, null, 2)}
                </Box>
              </CardContent>
            </Card>
            
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button 
                variant="outlined" 
                onClick={handleReset}
              >
                Upload Another
              </Button>
              <Button 
                variant="contained" 
                onClick={handleViewDocument}
              >
                View Document Details
              </Button>
            </Box>
          </Box>
        )}
      </Paper>
    </Box>
  );
}

export default DocumentUpload;
