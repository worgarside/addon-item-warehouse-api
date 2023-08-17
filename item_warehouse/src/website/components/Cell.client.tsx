"use client";

import React, { useRef, useState, useEffect } from "react";

import styles from "../styles/Cell.module.css";

import FullContentModal from "./FullContentModal.client";

const Cell: React.FC<{
  value: boolean | number | string | null;
  header: string;
}> = ({ value, header }) => {
  const [isOverflowing, setIsOverflowing] = useState(false);
  const cellRef = useRef<HTMLDivElement | null>(null);

  let content_string: string;

  if (value === null) {
    content_string = "null";
  } else {
    content_string = String(value);
  }

  useEffect(() => {
    if (cellRef.current) {
      const element = cellRef.current;
      if (element.scrollHeight > element.clientHeight) {
        setIsOverflowing(true);
      } else {
        setIsOverflowing(false);
      }
    }
  }, [content_string]);

  return (
    <td key={header} className={styles.cell}>
      <div className={styles.cellInner} ref={cellRef}>
        {isOverflowing ? (
          <>
            <div className={styles.scrollable}>
              <pre>
                <code
                  className={
                    content_string == "null" ? "text-muted" : styles.code
                  }
                >
                  {content_string}
                </code>
              </pre>
            </div>
            <FullContentModal content={content_string} header={header} />
          </>
        ) : (
          <code
            className={content_string == "null" ? "text-muted" : styles.code}
          >
            {content_string}
          </code>
        )}
      </div>
    </td>
  );
};

export default Cell;
