package GUI;

import java.awt.Dimension;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.KeyEvent;
import java.awt.event.KeyListener;
import java.text.DecimalFormat;
import java.util.Vector;

import javax.swing.*;
import javax.swing.border.TitledBorder;

public class ParameterChanger{
	@SuppressWarnings("unused")
	private double pmi; //inital parameter value 
	
	private double pmm; //current middel value;
	
	 
	private int order; // used for manual calibration
	
    private int  minorder =-7;
    private int  maxorder =2;
     
	private double oldpmm;
	private int oldorder;
	
	private JPanel paramP;
	private String name;
	private DecimalFormat df;
	
	public JTextField pmmTF;
	private JComboBox orderCB;
	
	public void setPMM(double pmm){
		this.pmm = pmm;
		
	}
	
	public void updateValue( double pmi,  int order){
		this.pmi = pmi; 
		this.order = order;
		oldorder = order;
		oldpmm = pmi;
		this.pmm = pmi;
		pmmTF.setText(String.valueOf(pmm));
 
		orderCB.setSelectedIndex(order-minorder);		
	}
	
	public void setEnabled(boolean enabled){
		pmmTF.setEnabled(enabled);
		orderCB.setEnabled(enabled);
	}

	public void restore(){
		pmm = oldpmm;
		order = oldorder;
		orderCB.setSelectedIndex(order-minorder);
		pmmTF.setText(String.valueOf(pmm));
	}
	
	public void storeOldValue(){
		//incase value is changed by mistake
		oldpmm = pmm;
		oldorder = order; 
	}
	
	public double getValue(){
		pmm = Double.valueOf(pmmTF.getText());
		return pmm;
	}
	
	 
	public ParameterChanger(String name, double pmi ,int order){
		this.name = name;
		this.pmi = pmi;		 
		this.order = order;
		this.pmm = pmi;
		 
		pmmTF = new JTextField(String.valueOf(pmm));
		pmmTF.addKeyListener(new ValueChanger());
	 
		 
		Vector<Integer> orderV = new Vector<Integer>();
		for(int i=minorder; i<=maxorder; i++){
			orderV.add(new Integer(i));
		}

		orderCB = new JComboBox(orderV);
		orderCB.setSelectedIndex(0);
		orderCB.addActionListener(new OrderSelector());
		
		df = new DecimalFormat("0.0000000");
		
		paramP = new JPanel();
		putTogether();
	}
		
	public class OrderSelector implements ActionListener{

		public void actionPerformed(ActionEvent arg0) {
			 
			order = orderCB.getSelectedIndex()+minorder;
			
		}
	}
	
	public class ValueChanger implements KeyListener{

		 //up, down, and enter keys

		public void keyPressed(KeyEvent e) {
			
			int keyCode = e.getKeyCode();
			//38 up
			//40 down
			//10 return
			if(keyCode == 38 ){
				pmm +=Math.pow(10.,(double)order);
				String values =df.format(pmm);
				pmmTF.setText(values );
			}else if (keyCode ==40){
				pmm -=Math.pow(10.,(double)order);
				String values =df.format(pmm);
				pmmTF.setText(values);
			}else if (keyCode ==10){
				try{
					double dvalue= Double.valueOf(pmmTF.getText());
					pmm = dvalue;
					}catch (Exception ee){
				
					}
			}
			
		}

		public void keyReleased(KeyEvent e) {
			
		}

		public void keyTyped(KeyEvent arg0) {
			
		}
		


	};
	
	public JPanel getPanel(){
		
		return paramP;
	};
	
	private void putTogether(){
		SpringLayout slayout = new SpringLayout();
		paramP.setLayout(slayout);
		 
		pmmTF.setPreferredSize(new Dimension(90, 20));
		slayout.putConstraint(SpringLayout.NORTH, pmmTF,0,SpringLayout.NORTH, paramP);
		slayout.putConstraint(SpringLayout.WEST,pmmTF, 0,SpringLayout.WEST, paramP);
		paramP.add(pmmTF);
		 
		orderCB.setPreferredSize(new Dimension(70, 20));
		slayout.putConstraint(SpringLayout.NORTH, orderCB,  0,SpringLayout.NORTH, paramP);
		slayout.putConstraint(SpringLayout.WEST,orderCB, 90,SpringLayout.WEST, paramP);
		paramP.add(orderCB);
		 
		TitledBorder title = BorderFactory.createTitledBorder(name);
		paramP.setBorder(title);
	};
	
	
	public void increase(){
		pmm +=order;
		pmmTF.setText(String.valueOf(pmm));
		
		//also check pmr
	};
	
	public void decrease(){
		pmm -=order;
		pmmTF.setText(String.valueOf(pmm));
		//also check pml
	};
}