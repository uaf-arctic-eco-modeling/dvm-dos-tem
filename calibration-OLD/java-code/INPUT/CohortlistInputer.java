package INPUT;

import java.io.File;
import java.io.IOException;

import ucar.ma2.Array;
import ucar.ma2.Index;
import ucar.nc2.NetcdfFile;
import ucar.nc2.Variable;

public class CohortlistInputer {
	
	//all-grids
	
	Array chtidA;
				
	public int init(String runchtlist){
		String filename = runchtlist;
		
		NetcdfFile ncfile = null;
		File ffile = new File(filename);
		if (ffile.exists()){
			try {
				ncfile = NetcdfFile.open(filename);

				Variable var = ncfile.findVariable("CHTID");
				chtidA = var.read();

			} catch (IOException ioe) {
					System.out.println(ioe.getMessage());
			} finally {
					if (ncfile != null) {
						try {
							ncfile.close();
						} catch (IOException ioee) {
							System.out.println(ioee.getMessage());
						}
					}
			}
		} else {   //file not exist
			System.out.println("Input file: "+filename+" NOT existed");
			System.exit(-1);
		}
	 
		return (int)chtidA.getSize();
	};

	public int getCHTID(int listindex){
		Index ind = chtidA.getIndex();
		return chtidA.getInt(ind.set(listindex));
	}; 

}

