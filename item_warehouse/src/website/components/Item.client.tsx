import React from "react";
import Cell from "./Cell.client";

interface ItemProps {
  item: Record<string, boolean | number | string>;
  index: number;
}

const Item: React.FC<ItemProps> = ({ item, index }) => {
  return (
    <tr key={index}>
      {Object.entries(item).map(([key, value]) => (
        <Cell content={String(value)} header={key} />
      ))}
    </tr>
  );
};

export default Item;
