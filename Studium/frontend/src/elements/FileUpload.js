import React, { useState, useContext, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import AuthContext from '../context/AuthContext';

import { ReactComponent as UploadIcon } from '../media/svg/upload.svg';
import { ReactComponent as Remove_Image } from '../media/svg/delete_1.svg';

import PDFIcon from '../media/png/upload_files/pdf.png';
import DOCIcon from '../media/png/upload_files/doc.png';
import PPTIcon from '../media/png/upload_files/ppt.png';
import XLSIcon from '../media/png/upload_files/xls.png';
import ZIPIcon from '../media/png/upload_files/zip.png';
import LOADIcon from '../media/png/upload_files/grey_loading.png';

const getIconByFormat = (format) => {
  switch (format) {
    case 'pdf':
      return PDFIcon;
    
    // Word
    case 'doc':
    case 'docm':
    case 'docx':
    case 'rtf':
      return DOCIcon;
    
    // Excel
    case 'xls':
    case 'xlsm':
    case 'xlsx':
    case 'csv':
      return XLSIcon;
    
    // PowerPoint
    case 'ppt':
    case 'pptm':
    case 'pptx':
      return PPTIcon;
    
    // Архивы
    case 'zip':
    case 'rar':
    case '7z':
      return ZIPIcon;
    
    default:
      return null;
  }
};

const getFileIcon = async (file, fileName) => {
  const format = fileName ? fileName.split('.').pop() : null;
  const isFileLink = typeof file === 'string' && file.startsWith('http');
  const isImageFile = !isFileLink && file && file.type.startsWith('image/');
  
  if (isImageFile) {
    try {
      return await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(file);
      });
    } catch (error) {
      console.error('Error generating preview:', error);
      return null;
    }
  }
  if (isFileLink) {
    const icon = getIconByFormat(format);
    if(icon){
      return icon;
    }
    return file;
  }

  return getIconByFormat(format);
};

function UploadComponent({ onChange, inputRef }) {
  return (
    <label className='upload_label'>
      <input  
        type='file' 
        ref={inputRef}
        accept=".pdf,.doc,.docx,.docm,.xlsx,.xls,.xlsm,.pptx,.ppt,.pptm,.jpg,.jpeg,.png,.zip,.rar,.txt" 
        onChange={onChange} 
        name='files'
        multiple 
        style={{ display: 'none' }} 
      />
      <div className='upload_item'>
        <UploadIcon className='upload_svg'/>
      </div>
    </label>
  );
}

function FileComponent({ value, onUpload, handleRemove, onChangeCheckBox, onError }) {
  const { accessToken } = useContext(AuthContext);

  const [loadProgress, setLoadProgress] = useState(0);
  const abortControllerRef = useRef(new AbortController());
  const [uploadError, setUploadError] = useState(null);
  const [icon, setIcon] = useState(null);
  
  useEffect(() => {
    return () => {
      abortControllerRef.current.abort();
    };
  }, []);

  useEffect(() => {
    const loadIcon = async () => {
      try {
        const icon = await getFileIcon(value.file, value.name);
        setIcon(icon);
      } catch (error) {
        console.error('Error loading icon:', error);
        setIcon(null);
      }
    };
    
    loadIcon();
  }, [value.file, value.name]);

  useEffect(() => {
    const errorUpload = (error) => {
      setUploadError(error.message || "Ошибка при загрузке файла");

      const errorMessage = `${error.response?.data?.message || error.message || "Ошибка при загрузке файла"}`;
      onError(errorMessage);
      handleRemove(value.file.name);
    };

    const uploadFile = async () => {
      if (!value.file || value.is_load) return;
  
      try {
        setUploadError(null);
        
        const metaResponse = await axios.post(
          "/api/ts/load/",
          {
            name: value.file.name,
            size: value.file.size,
            type: value.file.type.split(";")[0],
          },
          {
            headers: {'Authorization': `Bearer ${accessToken}`,
              "Content-Type": "application/json",
            },
          }
        );
  
        if (metaResponse.data?.status !== "success") {
          errorUpload(new Error("Не удалось получить ссылку для загрузки файла"));
        }
  
        const { file_path, upload_url } = metaResponse.data;
  
        const plainAxios = axios.create();

        const uploadResponse = await plainAxios.put(upload_url, value.file, {
          headers: {
            'Content-Type': value.file.type.split(';')[0],
          },
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setLoadProgress(percentCompleted);
          },
          signal: abortControllerRef.current.signal
        });

        if (uploadResponse.status !== 200) {
          throw new Error("Ошибка при загрузке файла");
        }

        onUpload({
          name: value.file.name,
          path: file_path,
        });
      } catch (error) {
        errorUpload(error);
      }
    };
  
    uploadFile();
  }, [value.file, value.is_load]);

  return (
    <div className='upload_item'>
      <div className='column_container'>
        <img className='upload_image' src={value.is_load ? icon : LOADIcon} />
        <div className='column_container' id='image_container'>
          {!value.is_load ? (
            <div className='column_container'>
              {uploadError ? (
                <div className='error_message'>{uploadError}</div>
              ) : (
                <>
                  <span className='upload_text'>{loadProgress}%</span>
                  <div className='progress-bar' style={{width: `${loadProgress}%`}}></div>
                </>
              )}
            </div>
          ) : (
            <>
              <p className='upload_text'>{value.name}</p>
              {onChangeCheckBox && (
                <p className='upload_text'>
                  Публичный:
                  <input 
                    className='upload_checkbox' 
                    type='checkbox' 
                    onChange={() => onChangeCheckBox(value.name)} 
                  />
                </p>
              )}
            </>
          )}
        </div>
        <button className="remove_button" type="button" onClick={() => handleRemove(value.name)}>
          <Remove_Image id="remove_button_svg" />
        </button>
      </div>
    </div>
  );
}

// Drag and Drop зона
function DragDropZone({ onFilesDrop, children, disabled = false, maxFiles = 15 }) {
  const [isDragging, setIsDragging] = useState(false);
  const dragCounter = useRef(0);

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDragIn = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current++;
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0 && !disabled) {
      setIsDragging(true);
    }
  }, [disabled]);

  const handleDragOut = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current--;
    if (dragCounter.current === 0) {
      setIsDragging(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    dragCounter.current = 0;

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0 && !disabled) {
      onFilesDrop(e.dataTransfer.files);
      e.dataTransfer.clearData();
    }
  }, [onFilesDrop, disabled]);

  useEffect(() => {
    window.addEventListener('dragover', handleDrag);
    window.addEventListener('drop', handleDrag);
    
    return () => {
      window.removeEventListener('dragover', handleDrag);
      window.removeEventListener('drop', handleDrag);
    };
  }, [handleDrag]);

  return (
    <div
      className={`drag-drop-zone ${isDragging ? 'drag-over' : ''} ${disabled ? 'disabled' : ''}`}
      onDragEnter={handleDragIn}
      onDragLeave={handleDragOut}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      style={{
        position: 'relative',
        minHeight: '200px',
        border: isDragging ? '2px dashed #007bff' : '2px dashed #ccc',
        borderRadius: '8px',
        padding: '20px',
        backgroundColor: isDragging ? '#f8f9fa' : '#fff',
        transition: 'all 0.3s ease',
        fontFamily: 'latoregular, latoregular other, sans-serif',
      }}
    >
      {children}
      
      {/* Overlay при перетаскивании */}
      {isDragging && (
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 123, 255, 0.1)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: '6px',
            zIndex: 10,
            fontFamily: 'latoregular, latoregular other, sans-serif',
          }}
        >
        </div>
      )}
    </div>
  );
}

export function FileUpload({ onChange, onError, maxFiles = 15, showPublicCheckbox = false, value }) {
  const [files, setFiles] = useState([]);
  const [freeSpace, setFreeSpace] = useState(maxFiles);
  const fileInputRef = useRef(null);
  const [columns, setColumns] = useState(getColumns(window.innerWidth));

  function getColumns(width) {
    if (width < 700) return 2;
    if (width < 900) return 3;
    return 5;
  }

  useEffect(() => {
    function handleResize() {
      setColumns(getColumns(window.innerWidth));
    }
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useEffect(() => {
    if (value && Array.isArray(value) && value.length > 0) {
      const prepared = value.map(f => ({
        file: f.file || null,
        name: f.name,
        path: f.path,
        size: f.size,
        is_public: String(f.is_public) === "true" || f.is_public === true,
        is_load: true,
      }));
      setFiles(prepared);
      setFreeSpace(maxFiles - prepared.length); 
    } else {
      setFiles([]);
      setFreeSpace(maxFiles);
    }
  }, [value, maxFiles]);  
  
  const rows = Math.ceil((files.length + 1) / columns) || 1;

  const processFiles = useCallback((fileList) => {
    try {
      const selectedFiles = Array.from(fileList);

      if (selectedFiles.length + files.length > maxFiles) {
        throw new Error(`Вы не можете загрузить более ${maxFiles} файлов`);
      }

      const validFiles = selectedFiles.filter(file => {
        try {
          return !files.some(f => f.name === file.name);
        } catch (error) {
          onError(error.message);
          return false;
        }
      });

      if (validFiles.length > 0) {
        setFiles(prevFiles => {
          const newFiles = [...prevFiles, ...validFiles.map(file => (
            { file, name: file.name, size: file.size, is_public: false, is_load: false }
          ))];
          onChange({ target: { name: 'files', value: newFiles } });
          return newFiles;
        });
      }
    } catch (error) {
      onError(error.message);
    } finally {
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  }, [files, maxFiles, onChange, onError]);

  const handleFileChange = (event) => {
    processFiles(event.target.files);
  };

  const handleDrop = useCallback((droppedFiles) => {
    processFiles(droppedFiles);
  }, [processFiles]);

  const handleFileUpload = (event) => {
    setFiles(prevFiles => {
      const updatedFiles = prevFiles.map(f =>
        f.name === event.name ? { ...f, path: event.path, is_load: true } : f
      );
      onChange({ target: { name: 'files', value: updatedFiles } });
      return updatedFiles;
    });
  };

  const handleFileRemove = (fileName) => {
    setFiles(prevFiles => {
      const updatedFiles = prevFiles.filter(fileObj => fileObj.name !== fileName);
      onChange({ target: { name: 'files', value: updatedFiles } });
      setFreeSpace(prevFreeSpace => prevFreeSpace + 1);
      return updatedFiles;
    });
  };

  const checkBoxOnChange = (fileName) => {
    setFiles(prevFiles => {
      const updatedFiles = prevFiles.map((fileObj) =>
        fileName === fileObj.name ? { ...fileObj, is_public: !fileObj.is_public } : fileObj);
      onChange({ target: { name: 'files', value: updatedFiles } });
      return updatedFiles;
    });
  };

  const isDragDropDisabled = files.length >= maxFiles;

  return (
    <DragDropZone onFilesDrop={handleDrop} disabled={isDragDropDisabled} maxFiles={maxFiles}>
      <div
        className='grid_container'
        id='upload_grid'
        style={{
          gridTemplateColumns: `repeat(${columns}, 1fr)`,
          gridTemplateRows: `repeat(${rows}, 1fr)`
        }}
      >
        {files.map((file) => (
          <FileComponent
            key={file.name}
            value={file}
            onUpload={handleFileUpload}
            handleRemove={handleFileRemove}
            onChangeCheckBox={showPublicCheckbox ? checkBoxOnChange : undefined}
            onError={onError}
          />
        ))}
        {files.length < maxFiles && (
          <UploadComponent
            onChange={handleFileChange}
            inputRef={fileInputRef}
          />
        )}
      </div>

      {/* Информация о Drag and Drop */}
      {files.length === 0 && (
        <div style={{textAlign: 'center'}}>
          <p id='grey_font' style={{marginTop: '25px', fontSize: '1.15rem',}}>Перетащите файлы сюда или нажмите на значок загрузки</p>
          <p id='grey_font' style={{ 
            fontSize: '1.0rem', 
            marginTop: '5px',
            fontFamily: 'latoregular, latoregular other, sans-serif',
          }}>
            Не более {maxFiles} файлов. Поддерживаемые форматы: PDF, DOC, XLS, PPT, JPG, PNG, ZIP, RAR
          </p>
        </div>
      )}
    </DragDropZone>
  );
}