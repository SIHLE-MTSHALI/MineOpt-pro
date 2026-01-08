import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const SensorChart = ({ title, data, dataKey, color = "#8884d8", unit }) => {
    return (
        <div className="sensor-chart card">
            <h3>{title}</h3>
            <div style={{ width: '100%', height: 300 }}>
                {(!data || data.length === 0) ? (
                    <div className="no-data">No data available</div>
                ) : (
                    <ResponsiveContainer>
                        <LineChart data={data}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="time" />
                            <YAxis unit={unit} />
                            <Tooltip />
                            <Legend />
                            <Line
                                type="monotone"
                                dataKey={dataKey}
                                stroke={color}
                                activeDot={{ r: 8 }}
                                name={title}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                )}
            </div>
        </div>
    );
};

export default SensorChart;
