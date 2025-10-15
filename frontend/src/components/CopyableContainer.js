import React, { useRef, useState, useEffect } from 'react';
import * as htmlToImage from 'html-to-image';
import './styles/tableStyles.css';

/**
 * A reusable component that wraps any content and provides functionality
 * to copy that content as an image.
 * 
 * @param {Object} props
 * @param {React.ReactNode} props.children - The content to be rendered and copied
 * @param {string} props.title - The title to display above the content
 * @param {string} props.fileName - The filename to use when downloading (without extension)
 * @param {string} props.className - Additional class names to apply to the wrapper
 * @param {Object} props.style - Additional inline styles for the wrapper
 */
const CopyableContainer = ({ 
  children, 
  title, 
  fileName = 'image', 
  className = '', 
  style = {} 
}) => {
  const containerRef = useRef(null);
  const [copying, setCopying] = useState(false);
  const [copySuccess, setCopySuccess] = useState(false);

  // Reset success indicator after 3 seconds
  useEffect(() => {
    let timer;
    if (copySuccess) {
      timer = setTimeout(() => {
        setCopySuccess(false);
      }, 3000);
    }
    return () => clearTimeout(timer);
  }, [copySuccess]);

  const handleCopyAsImage = async () => {
    if (!containerRef.current) return;
    try {
      setCopying(true);

      // Get reference to the copy button element
      const copyBtn = containerRef.current.querySelector('.copy-btn');
      // Hide button during capture
      const originalDisplay = copyBtn ? copyBtn.style.display : null;
      if (copyBtn) {
        copyBtn.style.display = 'none';
      }

      // Store original styles to restore later
      const originalStyle = containerRef.current.style.cssText;
      
      // Apply inline styles for the image capture
      containerRef.current.style.margin = '0';
      containerRef.current.style.paddingLeft = '5px';
      containerRef.current.style.paddingRight = '5px';
      containerRef.current.style.paddingTop = '0';
      containerRef.current.style.paddingBottom = '5px'; // Add padding to the bottom
      
      // create PNG data URL from the element
      const dataUrl = await htmlToImage.toPng(containerRef.current);
      
      // Restore the original styles
      containerRef.current.style.cssText = originalStyle;
      
      // Restore the button display
      if (copyBtn) {
        copyBtn.style.display = originalDisplay || '';
      }

      // convert data URL -> Blob
      const resp = await fetch(dataUrl);
      const blob = await resp.blob();

      // Preferred: write image to clipboard (modern Chrome/Edge)
      if (
        navigator.clipboard &&
        typeof window !== "undefined" &&
        typeof window.ClipboardItem !== "undefined"
      ) {
        try {
          const item = new window.ClipboardItem({
            "image/png": blob,
          });
          await navigator.clipboard.write([item]);
          setCopySuccess(true);
          return;
        } catch (err) {
          console.warn(
            "Navigator.clipboard.write failed, falling back to download:",
            err
          );
          // fallthrough to fallback download
        }
      }

      // Fallback: download the image so the user can manually copy/share it
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${fileName}.png`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      setCopySuccess(true);
    } catch (err) {
      console.error("Error copying as image:", err);
    } finally {
      setCopying(false);
    }
  };

  return (
    <div className={`wrapper-wide relative copyable-content ${className}`} ref={containerRef} style={style}>
      <div className="header-controls-row">
        {title && <h2 className="text-xl font-semibold mb-4">{title}</h2>}
        <button
          onClick={handleCopyAsImage}
          className={`copy-btn ${copySuccess ? "copy-success" : ""}`}
          disabled={copying}
          title={copySuccess ? "Copied!" : "Copy as image"}
        >
          {copying ? "⏳ Copying..." : copySuccess ? "✅ Copied!" : "📋 Copy as Image"}
        </button>
      </div>
      <div className="content-with-padding">
        {children}
      </div>
    </div>
  );
};

export default CopyableContainer;