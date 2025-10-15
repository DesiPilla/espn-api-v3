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
        const copyBtn = containerRef.current.querySelector(".copy-btn");
        // Hide button during capture
        const originalDisplay = copyBtn ? copyBtn.style.display : null;
        if (copyBtn) {
            copyBtn.style.display = "none";
        }

        // Store original styles to restore later
        const originalStyle = containerRef.current.style.cssText;

        // Get the table element
        const tableElement = containerRef.current.querySelector("table");
        let originalTableStyle = null;

        if (tableElement) {
            // Store original table styles
            originalTableStyle = tableElement.style.cssText;

            // Determine if this is a wide table that needs special handling
            const columnCount =
                tableElement.querySelectorAll("thead th").length;

            // Apply special handling for wide tables (like RankDistributionTable)
            if (columnCount > 5) {
                tableElement.style.width = "auto";
                tableElement.style.tableLayout = "auto";

                // Make sure text doesn't wrap
                const cells = tableElement.querySelectorAll("th, td");
                cells.forEach((cell) => {
                    cell.style.whiteSpace = "nowrap";
                    cell.style.padding = "5px";
                });
            }
        }

        // Apply inline styles for the image capture
        containerRef.current.style.margin = "0";
        containerRef.current.style.paddingLeft = "10px";
        containerRef.current.style.paddingRight = "10px";
        containerRef.current.style.paddingTop = "0";
        containerRef.current.style.paddingBottom = "0"; // Increased bottom padding
        containerRef.current.style.maxWidth = "none";

        // Calculate the actual width needed
        let captureWidth = containerRef.current.scrollWidth + 20; // Add padding

        // create PNG data URL from the element with higher resolution
        const dataUrl = await htmlToImage.toPng(containerRef.current, {
            pixelRatio: 2.0, // Increase resolution - use 2.0 for double resolution
            quality: 1.0, // Highest quality
            width: captureWidth,
            height: containerRef.current.scrollHeight + 20,
        });

        // Restore the original styles
        containerRef.current.style.cssText = originalStyle;

        // Restore table styles if modified
        if (tableElement && originalTableStyle) {
            tableElement.style.cssText = originalTableStyle;
        }

        // Restore the button display
        if (copyBtn) {
            copyBtn.style.display = originalDisplay || "";
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